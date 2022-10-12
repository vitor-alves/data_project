import csv

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.sftp.operators.sftp import SFTPOperator
from airflow.providers.sftp.sensors.sftp import SFTPSensor
from airflow.utils.dates import days_ago
from airflow.hooks.mysql_hook import MySqlHook


def process_file(**kwargs):
    templates_dict = kwargs.get("templates_dict")
    input_file = templates_dict.get("input_file")
    output_file = templates_dict.get("output_file")
    output_rows = []
    with open(input_file, newline='') as csv_file:
        csv_reader = csv.reader(csv_file)
        # skip header
        next(csv_reader) 
        for row in csv_reader:
            output_rows.append(row)
    with open(output_file, "w", newline='') as csv_file:
        # write csv and change delimiter to 'tab'
        writer = csv.writer(csv_file, delimiter='\t', lineterminator='\n')
        writer.writerows(output_rows)

def bulk_load_sql(table_name, **kwargs):
    local_filepath = "/tmp/files/trips_output.tsv"
    conn = MySqlHook(mysql_conn_id='my_mysql_server')
    conn.bulk_load_custom(table=table_name, tmp_file=local_filepath, duplicate_key_handling='IGNORE')
    return table_name

def truncate_table_mysql(table_name, **kwargs):
    conn = MySqlHook(mysql_conn_id='my_mysql_server')
    cn = conn.get_conn()
    c = cn.cursor()
    c.execute("TRUNCATE TABLE {}".format(table_name))
    cn.commit()
    c.close()
    cn.close()
    return table_name

def process_stg_to_final(stg_table_name, final_table_name, **kwargs):
    conn = MySqlHook(mysql_conn_id='my_mysql_server')
    cn = conn.get_conn()
    c = cn.cursor()
    c.execute("insert into {} (region,origin_coord,destination_coord,datetime) select distinct region,ST_GeomFromText(origin_coord),ST_GeomFromText(destination_coord),datetime from {}".format(final_table_name, stg_table_name))
    cn.commit()
    c.close()
    cn.close()
    return final_table_name

with DAG("ingest_data_trips_to_mysql",
         schedule_interval=None,
         is_paused_upon_creation=False,
         start_date=days_ago(2)) as dag:

    wait_for_input_file = SFTPSensor(task_id="check-for-file",
                                     sftp_conn_id="my_sftp_server",
                                     path="/upload/raw_data/trips.csv",
                                     poke_interval=10)

    download_file = SFTPOperator(
        task_id="get-file",
        ssh_conn_id="my_sftp_server",
        remote_filepath="/upload/raw_data/trips.csv",
        local_filepath="/tmp/files/trips_input.csv",
        operation="get",
        create_intermediate_dirs=True
    )

    process_file = PythonOperator(task_id="process-file",
                                  templates_dict={
                                      "input_file": "/tmp/files/trips_input.csv",
                                      "output_file": "/tmp/files/trips_output.tsv"
                                  },
                                  python_callable=process_file)

    upload_file = SFTPOperator(
        task_id="put-file",
        ssh_conn_id="my_sftp_server",
        remote_filepath="/upload/out_data/trips_output.tsv",
        local_filepath="/tmp/files/trips_output.tsv",
        operation="put"
    )

    truncate_sink_mysql = PythonOperator(
        task_id='truncate-sink-mysql',
        provide_context=True,
        python_callable=truncate_table_mysql,
        op_kwargs={'table_name': 'stg_trips'},
        dag=dag)

    load_file_to_mysql = PythonOperator(
        task_id='file-to-mysql',
        provide_context=True,
        python_callable=bulk_load_sql,
        op_kwargs={'table_name': 'stg_trips'},
        dag=dag)

    process_stg_to_final = PythonOperator(
        task_id='process_stg_to_final',
        provide_context=True,
        python_callable=process_stg_to_final,
        op_kwargs={'stg_table_name': 'stg_trips', 'final_table_name': 'trips'},
        dag=dag)

    wait_for_input_file >> download_file >> process_file >> upload_file >> truncate_sink_mysql >> load_file_to_mysql >> process_stg_to_final

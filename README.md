### Deployment instructions 
The application is entirely deployed in Docker for ease of deployment.
#### Dependencies
- Docker
- Docker Compose

Note: this application has been succesfully tested with docker compose version 2.6.0 and docker version 20.10.17 in Ubuntu Linux 20.04 LTS and docker compose version 2.7.0 and docker version 20.10.17 on MacOS. 

DO NOT use old versions of docker or docker compose because it may fail to run the containers or read the .yaml configuration files correctly. If docker containers are not starting, or docker compose is complaining about .yaml files being incorrect, this is most likely the the issue. 

#### Install Docker (if not installed already)
https://docs.docker.com/engine/install/


#### Install Docker Compose (if not installed already)
https://docs.docker.com/compose/install/

#### Ensure you user has permissions to run docker to manage docker as a non-root user
The docker and docker compose compose commands below require your non-root user to be part of the docker group in the operating system. 
To add your user to the docker group follow the instructions in the following link.

https://docs.docker.com/engine/install/linux-postinstall/

Ensure that the docker hello-world container is running correctly before continuing. In case hello-world fails, follow the steps in the link above again because docker is not correctly set up in your machine.

    $ docker run hello-world

Alternatively, you may also want to run the commands with root privileges by adding "sudo" to all docker and docker compose commands, such as 

    $ sudo docker run hello-world

#### Create docker external network used by containers to communicate with each other
Open a terminal window and run:

    $ docker network create global_network

#### Start SFTP service
Open a terminal window in the project root folder and run:

    $ cd sftp

    $ docker-compose up

#### Start MySQL service
Open a terminal window in the project root folder and run:

    $ cd mysql

    $ docker-compose up

#### Start Apache Airflow service
Open a terminal window in the project root folder and run:

    $ cd airflow

    $ docker-compose up

### How to trigger Airflow data pipelines to process input data (via Web UI)
Ensure SFTP, MySQL and Apache Airflow docker services are running by running the command below. In case any of the services is not running, go back to the previous section, Deployment instructions.

    $ docker ps

The starting point to the data pipeline is Airflow. It is responsible for orchestrating the data pipeline from start (consuming files from SFTP) to finish (loading data into the database).

To consume the .csv input file, transform, and save the data in the database you first need to open Airflow webpage and trigger the data pipeline.

Open your browser and head over to Airflow's login page at http://localhost:18080

Note: in case you can't access http://localhost:18080 verify if the Airflow Docker container is running correctly. 

    user: airflow
    password: airflow

You should be able to see the DAGs listed as in the following picture

![see file airflow_dags.png if you can't see the picture here](airflow_dags.png "airflow_dags.png")

To process the input trips.csv file, you need to trigger the DAG by clicking on the blue "play" button and then choosing the option to "Trigger DAG".

This will start the ingestion of the input .csv file and start populating the database. 
After this process, the content of the input file will be available in the corresponding database table: 

    trips.csv -> app_db.trips

After triggering all Airflow DAGs you should be able to connect to the MySQL database with your tool of choice (e.g. MySQL Workbench, DataGrip, DBeaver) and query the newly populated tables.

    MySQL connection information
    URL: localhost
    Port: 33061
    user: root
    password: 2ujajd28jAXZAfPamg
Note: root database user is being used because this is a test. It should never be used in production.

More details about the implementation below in the "Architecture explained" section

### How to trigger Airflow data pipelines to process input data (via REST API)
Alternatively to the process described above to trigger the Airflow pipeline via the Web UI, you can trigger it via console by calling Airflow's REST API.

    curl --location --request POST 'http://localhost:18080/api/v1/dags/ingest_data_trips_to_mysql/dagRuns' \
    --header 'Authorization: Basic YWlyZmxvdzphaXJmbG93' \
    --header 'Content-Type: application/json' \
    --header 'Cookie: session=a8a9613a-ab86-4e3f-ad2c-6874d0359117.y-D3KIZxNBz7x1pKBnofDr4yze4' \
    --data-raw '{
        "conf": { }
    }'

### Architecture explained
#### Diagram
![see file current_implementation.png if you can't see the picture here](current_implementation.png "current_implementation.png")

#### Data pipeline main services
- SFTP
- Airflow
- MySQL

#### How the data pipeline works
Airflow is the orchestrator responsible for conducting the entire data flow of the file being processed. It contains a DAG, which determine the steps in which the data processing should be done. DAGs execution can be scheduled, but in this project it should be triggered manually.

Below is the only available DAGs

    ingest_data_trips_to_mysql 
    
Those are the tasks executed by this DAG (in that order)
    
    wait_for_input_file >> download_file >> process_file >> upload_file >> truncate_sink_mysql >> load_file_to_mysql >> process_stg_to_final

Once a DAG is triggered, Airflow watches the SFTP service, waiting for trips.csv file to be available. Once it is available, it then downloads the file from the SFTP server and saves it locally. It then processes this file and converts the input file into a standardized .tsv file that is saved both locally and in an SFTP server for backup or reprocessing if nedded (cloud storages such as AWS S3 could also be used). After that, Airflow copies the content of this processed .tsv file and saves the data in an empty staging table in MySQL. Then comes the last step that uses SQL queries to cleanse and transform the staging data and insert into the final production table.

## Mandatory features checklist
1. **There must be an automated process to ingest and store the data.**
    * Airflow is being used to ingest and store the data, and can be triggered via 3 ways: REST API, Web UI, or scheduled
2. **Trips with similar origin, destination, and time of day should be grouped together.**
    * Done by selecting only distinct records based on origin, destination and time of day when moving the data from the "stg_trips" staging table to the final "trips" table.

3. **Develop a way to obtain the weekly average number of trips for an area, defined by a bounding box (given by coordinates) or by a region.**
    * Assuming a bounding box similar to the drawing below, with points (lon1,lat1), (lon2,lat2), (lon3,lat3), (lon4,lat4), you can calculate the weekly average number of trips with a simple SQL query, stored in sql_queries/weekly_average_num_trips.sql. To check the query, please open that file.
![see file bounding_box.png if you can't see the picture here](bounding_box.png "bounding_box.png")
    * To obtain the result, we need to run the query in MySQL. A quick way to do it is to use the console to connect to the "mysql" container, and run the "mysql" command with the query we want to execute as the content of the "-e" (--execute) parameter. The reason I'm choosing this solution is because this is quick to develop, but it's definitely not the solution I would choose if this was an actual production-level project because it is suitable for SQL injection, a little hard to use and understand, and too error prone because the user needs to modify the command to set the variables. For a production-level project I would encapsulate the access to the database behind a secure and user friendly REST API.
    
Modify the following command with the values you want for @lon1,@lat1,@lon2,@lat2,@lon3,@lat3,@lon4,@lat4, and @region, then execute it in the console.  
MySQL will ask for the user password. The password is 2ujajd28jAXZAfPamg

    docker exec -it mysql bash -c 'mysql -u root -p --database app_db --batch -e "set @lon1 = 0; set @lat1 = 0; set @lon2 = 30.0; set @lat2 = 0; set @lon3 = 0; set @lat3 = 50.0; set @lon4 = 30.0; set @lat4 = 50.0; set @region = \"Prague\"; source /sql_queries/weekly_average_num_trips.sql;"'

4. **Develop a way to inform the user about the status of the data ingestion without using a polling solution.**
    * The user can check the status of the data ingestion at http://localhost:18080/dags/ingest_data_trips_to_mysql/grid
    * ![see file airflow_status_page.png if you can't see the picture here](airflow_status_page.png "airflow_status_page.png")
5. **The solution should be scalable to 100 million entries. It is encouraged to simplify the data by a data model. Please add proof that the solution is scalable.**
    * The solution is scalable to 100 milion entries. Lets analyze each component and see if any of them could be a bottleneck to scale up to 100 milion entries.
        * SFTP and file size. The sample file is 12.9kB and contains 100 rows. That being said, we can estimate that a file with 100 milion rows would be 129mB. This a very reasonable size for the SFTP server to serve and for Airflow to consume. SFTP is capable of transfering files much greater than that, so file size and SFTP is are not a bottleneck. 
    * Airflow. The only part of the DAG that is affected by the file size are the parts associated with consuming the files from SFTP and moving the file into the MySQL container for further ingestion of the file. Considering a 100 milion file would be only 129 mB, this is not a bottleneck.
    * MySQL. MySQL is a database well known for being able to handle tables with over 100M rows. This is well documented online, and I personally have managed tables even bigger in MySQL before. There are some caveats, but it's 100% possible and a viable solution. You would need to create indexes on some of the columns, possibly would want to partition the table by date, and maybe do some SQL tunning to improve the SQL queries that access that table, but good performance certanly can be achieved. MySQL is certanly not the best database for this job, a MPP Database (e.g. Amazon Redshift, Google BigQuery, Amazon Synapse Analytics) would but better, but MySQL is free, reliable, and can be considered good enough for the business problem we are analyzing here. Regarding the data model, a single trips table with 100M rows as currently implemented is sufficient. However, my suggestion, in case this was a production environment, would be to evolve that into an actual data warehouse solution by using Kimball dimensional modeling techniques (a Star Schema with dimension and fact tables).
6. **Use a SQL database.**
    * Requirement fulfilled. - I'm using MySQL.

## Bonus features checklist
1. **Containerize your solution.**
    - Requirement fulfilled. All services are deployed using docker.
2. **Sketch up how you would set up the application using any cloud provider (AWS, Google Cloud, etc).**
    - Not taking the cost into consideration, I would change things a bit compared to the current implementation. I would use use AWS Transfer for SFTP, Airbyte for Extract and Load phases, Amazon Redshift for the Data Warehouse, dbt (in AWS) for data transformation, and Tableau for Analytics and BI. 
    - ![see file production_implementation.png if you can't see the picture here. Alternatively, check https://imgur.com/hs4ExM7](production_implementation.png "production_implementation.png")

- **Include a .sql file with queries to answer these questions**
    - **From the two most commonly appearing regions, which is the latest datasource?**
        - Done. The most commonly appearing region is Turin, and the latest data source is pt_search_app. The second most commonly appearing region is Prague, and the latest datasource is cheap_mobile.
        - Code available at sql_queries/most_common_region_latest_datasource.sql
    - **What regions has the "cheap_mobile" datasource appeared in?**
        - Done. cheap_mobile appears in Prague, Turin, and Hamburg.
        - Code available at sql_queries/regions_where_cheap_mobile_appeared.sql





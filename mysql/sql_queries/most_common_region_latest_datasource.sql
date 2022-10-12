with region_rank as (
    select region,
           datasource,
           datetime,
           count(*) over(partition by region) as count_in_region,
           row_number() over (partition by region order by datetime desc) as rank_datetime_in_region
    from stg_trips
)
select region, datasource as latest_datasource
from (
    select region,
           datasource,
           datetime,
           row_number() over (order by count_in_region desc) as rank_region_counts
    from region_rank
    where rank_datetime_in_region = 1
) t
where t.rank_region_counts in (1,2);
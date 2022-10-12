prepare stmt from 'with trips_per_week as (
    select count(*) num_trips, week(datetime) week
    from trips
    where
    region = ?
    or
    (
        ST_X(origin_coord) BETWEEN LEAST(?,?,?,?) AND GREATEST(?,?,?,?)
        AND
        ST_Y(origin_coord) BETWEEN LEAST(?,?,?,?) AND GREATEST(?,?,?,?)
    )
    group by week(datetime)
)
select sum(num_trips)/count(*) as "Average Trips per Week"
from trips_per_week;';
execute stmt using @region,@x1,@x2,@x3,@x4,@x1,@x2,@x3,@x4,@y1,@y2,@y3,@y4,@y1,@y2,@y3,@y4;
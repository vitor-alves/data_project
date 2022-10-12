prepare stmt from 'with trips_per_week as (
    select count(*) num_trips, week(datetime) week
    from trips
WHERE
(
    -- Contains the region
    region = ?
)
OR
(
    -- Contains the origin_coord
    MBRContains(
        POLYGON(LINESTRING(point(?,?),point(?,?),point(?,?),point(?,?),point(?,?))),
            origin_coord)
    -- Contains the destination_coord
    AND MBRContains(
        POLYGON(LINESTRING(point(?,?),point(?,?),point(?,?),point(?,?),point(?,?))),
            destination_coord)
)
    group by week(datetime)
)
select sum(num_trips)/count(*) as "Average Trips per Week"
from trips_per_week;';
execute stmt using @region, @lon1, @lat1, @lon2, @lat2, @lon3, @lat3, @lon4, @lat4, @lon1, @lat1, @lon1, @lat1, @lon2, @lat2, @lon3, @lat3, @lon4, @lat4, @lon1, @lat1;
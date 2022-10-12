prepare stmt from 'SELECT *
FROM trips
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
;';
execute stmt using @region, @lon1, @lat1, @lon2, @lat2, @lon3, @lat3, @lon4, @lat4, @lon1, @lat1, @lon1, @lat1, @lon2, @lat2, @lon3, @lat3, @lon4, @lat4, @lon1, @lat1;
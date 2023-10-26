create temp view export as

WITH

    pre AS (
        SELECT ts, session_id, tls_type
        FROM pkt
                 JOIN capture USING (capture_id)
        WHERE
                capture.name = :'name'
          AND capture."type" = 'post'
          AND pkt.tls_type = 'ServerHello'
    )

   , intermed AS (

    select ts,
           session_id,
           tls_type,
           lead(ts) over (order by ts) as next_client_hello
    from (SELECT ts, session_id, tls_type, row_number() over (partition by session_id) as c
          FROM pkt
                   JOIN capture USING (capture_id)
          WHERE capture.name = :'name'
            AND capture."type" = 'pre'
            AND pkt.tls_type = 'ClientHello'
          ORDER BY ts ASC) as yolo
    where c = 1
)

   , post AS (
    SELECT ts, session_id, tls_prot
    FROM pkt
             JOIN capture USING (capture_id)
    WHERE
            capture.name = :'name'
      AND capture."type" = 'pre'
      AND pkt.tls_prot = 'ChangeCipherSpec'
),

    pre_join AS (
        SELECT
            pre.ts as prets,
            intermed.ts as intermedts,
            intermed.next_client_hello as next_client_hello,
            pre.session_id as session_id
        FROM pre JOIN intermed USING (session_id)
        WHERE pre.ts > intermed.ts
          AND pre.ts < intermed.ts + 5 * 1e9
    )

SELECT *, count(*) FROM (
    SELECT mpcaps.latency_bucket
    FROM (
	SELECT
        row_number() over (partition by pre_join.session_id) as c,
        pre_join.prets AS prets,
		post.ts as postts,
            ((post.ts - pre_join.prets) / :'bucket_size' ) * :'bucket_size' AS latency_bucket
        FROM  pre_join JOIN  post ON pre_join.prets < post.ts AND pre_join.next_client_hello > post.ts
        WHERE post.ts > pre_join.prets
            AND post.ts < pre_join.prets + 5 * 1e9
            AND post.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT MIN(ts) from post))::bigint
        ORDER BY pre_join.prets ASC
    ) AS mpcaps
    WHERE mpcaps.c = 1
) AS histogram
GROUP BY histogram.latency_bucket
ORDER BY histogram.latency_bucket ASC
;

\copy (select * from export order by latency_bucket) to pstdout csv header

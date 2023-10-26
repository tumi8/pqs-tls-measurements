create temp view export as

WITH

    pre AS (

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
)


SELECT *, count(*) FROM (
                            SELECT mpcaps.latency_bucket
                            FROM (
                                     SELECT
                                         pre.ts AS prets,
                                         post.ts as postts,
                                         row_number() over (partition by pre.next_client_hello) as c,
                                         ((post.ts - pre.ts) / :'bucket_size' ) * :'bucket_size' AS latency_bucket
                                     FROM  pre JOIN  post ON pre.ts < post.ts AND pre.next_client_hello > post.ts
                                     WHERE post.ts > pre.ts
                                       AND post.ts < pre.ts + 5 * 1e9
                                       AND post.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT MIN(ts) from post))::bigint
                                     ORDER BY post.ts DESC
                                 ) AS mpcaps
                            WHERE c = 1
                            ORDER BY prets
                        ) AS histogram
GROUP BY histogram.latency_bucket
ORDER BY histogram.latency_bucket ASC

;

\copy (select * from export order by latency_bucket) to pstdout csv header

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


SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY mpcaps.latency) as latency_median
FROM (
         SELECT
                 post.ts - pre.ts as latency,
                 row_number() over (partition by pre.next_client_hello) as c
         FROM  pre JOIN  post ON pre.ts < post.ts AND pre.next_client_hello > post.ts
         WHERE post.ts > pre.ts
           AND post.ts < pre.ts + 5 * 1e9
           AND post.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT MIN(ts) from post))::bigint
         ORDER BY post.ts DESC
     ) AS mpcaps
WHERE c = 1
;

\copy (select * from export ) to pstdout csv header

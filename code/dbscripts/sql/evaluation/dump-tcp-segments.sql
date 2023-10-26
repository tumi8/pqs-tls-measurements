create temp view exporter as

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
),

    server AS (
        SELECT ts
        FROM pkt
                 JOIN capture USING (capture_id)
        WHERE
                capture.name = :'name'
          AND capture."type" = 'post'
          AND pkt.tcp_data_len > 0
        ORDER BY ts ASC
    )

   , border AS (SELECT
                        pre.ts AS prets,
                        post.ts as postts,
                        pre.session_id as session_id
                FROM  pre JOIN  post  ON pre.ts < post.ts AND pre.next_client_hello > post.ts
                WHERE post.ts > pre.ts
                  AND post.ts < pre.ts + 5 * 1e9
                  AND post.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT MIN(ts) from post))::bigint)
   , limited AS (SELECT * FROM border LIMIT 1)

SELECT count(*) as packets FROM server JOIN limited ON limited.prets < server.ts AND limited.postts > server.ts GROUP BY limited.prets;


\copy (SELECT * FROM exporter) to pstdout csv header

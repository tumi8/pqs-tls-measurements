create unlogged table if not exists capture (capture_id serial primary key, name text, "type" text);
create unlogged table if not exists pkt (capture_id int references capture(capture_id), ts int8, src_ip text, dst_ip text, len int, header_len int, src_port int8, dst_port int8, seq text, ack text, flag text, tls_prot text, tls_type text, id_length text, session_id text, tcp_data_len smallint);
create unique index if not exists capture_name_type_idx on capture (name, "type");
create index if not exists pkt_capture_id_idx ON pkt using brin (capture_id);

ALTER TABLE capture SET (
  autovacuum_enabled = false, toast.autovacuum_enabled = false
);

ALTER TABLE pkt SET (
  autovacuum_enabled = false, toast.autovacuum_enabled = false
);

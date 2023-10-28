create unique index if not exists capture_name_type_idx on capture (name, "type");
create index if not exists pkt_capture_id_idx ON pkt using brin (capture_id);
create index if not exists pkt_ts_idx ON pkt using brin (ts);

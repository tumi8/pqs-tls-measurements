insert into capture (name, "type")
	values (:'name', :'type')
	returning capture_id as capture_id
\gset import_ 

create temporary table import (ts int8, src_ip text, dst_ip text, len int, header_len int, src_port int8, dst_port int8, seq text, ack text, flag text, tls_prot text, tls_type text, id_length text, session_id text, tcp_data_len smallint);

\copy import from pstdin

insert into pkt (capture_id, ts, src_ip, dst_ip, len, header_len, src_port, dst_port, seq, ack, flag, tls_prot, tls_type, id_length, session_id, tcp_data_len) select :import_capture_id, ts, src_ip, dst_ip, len, header_len, src_port, dst_port, seq, ack, flag, tls_prot, tls_type, id_length, session_id, tcp_data_len from import;

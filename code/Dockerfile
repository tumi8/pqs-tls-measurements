FROM debian:bullseye

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y python3 zstd parallel postgresql postgresql-client git \
    python3-pip python3-click python3-yaml python3-pandas linux-perf

RUN pip3 install pypacker==5.4  netifaces==0.11.0

RUN mkdir -p /opt
WORKDIR /opt

COPY dbscripts /opt/dbscripts/
COPY evaluator/evaluate.sh /opt/
COPY evaluator/csvgenerator_client.py /opt/

ENTRYPOINT /opt/evaluate.sh

FROM debian:bullseye

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y zstd

RUN mkdir -p /opt
WORKDIR /opt

COPY run.sh /opt/

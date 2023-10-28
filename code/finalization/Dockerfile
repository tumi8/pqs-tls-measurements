FROM debian:bullseye

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y python3 \
    python3-pip python3-click python3-pandas python3-seaborn python3-numpy python3-matplotlib

WORKDIR /opt
COPY *.py /opt/
COPY run.sh /opt/
ENTRYPOINT /opt/run.sh
FROM debian:bullseye

# Docker Arguments
ARG OPENSSL_BRANCH
ARG OPENSSL_REPO
ARG LIBOQS_COMMIT

# liboqs build type variant; maximum portability of image:
ENV LIBOQS_BUILD_DEFINES "-DOQS_DIST_BUILD=ON"
ENV OPENSSL_BUILD_DEFINES "-DOQS_DEFAULT_GROUPS=p384_kyber768:X25519:kyber768"
ENV OPENSSL_PATH /opt/openssl
ENV OPENSSL_SRC_PATH /opt/openssl-src
ENV MAKE_DEFINES "-j 18"
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y build-essential iproute2 \
            libtool automake autoconf cmake ninja-build dnsutils tcpdump \
            make \
            openssl libssl-dev \
            git wget libpcre3 libpcre3-dev

RUN mkdir -p /opt $OPENSSL_PATH $OPENSSL_SRC_PATH /out
WORKDIR /opt

RUN git clone --branch main https://github.com/open-quantum-safe/liboqs && \
    git clone --depth 1 --branch ${OPENSSL_BRANCH} ${OPENSSL_REPO} ${OPENSSL_SRC_PATH}

WORKDIR /opt/liboqs

# Build LibOQS
RUN git checkout $LIBOQS_COMMIT && mkdir -p build-static
WORKDIR /opt/liboqs/build-static
RUN cmake -G"Ninja" ${LIBOQS_BUILD_DEFINES} -DBUILD_SHARED_LIBS=OFF -DCMAKE_INSTALL_PREFIX=${OPENSSL_SRC_PATH}/oqs ..
RUN ninja
RUN ninja install

WORKDIR /opt/liboqs

RUN mkdir -p build && cd build  && \
    cmake -G"Ninja" .. ${LIBOQS_BUILD_DEFINES} -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/opt/ossl-src/oqs && \
    ninja install

# build openssl
WORKDIR $OPENSSL_SRC_PATH
ENV LDFLAGS "-Wl,-rpath -Wl,${OPENSSL_PATH}/lib"

RUN ./config shared ${OPENSSL_BUILD_DEFINES} --prefix=${OPENSSL_PATH} && \
    make generate_crypto_objects && \
    make ${MAKE_DEFINES} && \
    make install

ARG CPU_PROFILING
RUN if [ "$CPU_PROFILING" = "True" ]; then \
    apt-get install -y linux-perf; fi

ENV OPENSSL "${OPENSSL_PATH}/bin/openssl"
ENV OPENSSL_CNF "${OPENSSL_PATH}/ssl/openssl.cnf"

WORKDIR /opt
COPY measurement-openssl-client.sh /opt/
COPY measurement-openssl-server.sh /opt/

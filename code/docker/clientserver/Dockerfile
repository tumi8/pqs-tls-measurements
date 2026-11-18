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

# Bullseye security packages have moved off the live mirror. Keep the
# historical distribution and signed packages available for reproduction.
ARG DEBIAN_SNAPSHOT=20260831T235959Z
RUN printf '%s\n' \
    "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT}/ bullseye main" \
    "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT}/ bullseye-security main" \
    > /etc/apt/sources.list && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y build-essential iproute2 \
            libtool automake autoconf cmake ninja-build dnsutils tcpdump \
            make \
            openssl libssl-dev \
            git wget libpcre3 libpcre3-dev

RUN mkdir -p /opt $OPENSSL_PATH $OPENSSL_SRC_PATH /out
WORKDIR /opt

RUN git init --quiet liboqs && \
    git -C liboqs remote add origin https://github.com/open-quantum-safe/liboqs && \
    git -C liboqs fetch --progress --depth 1 origin ${LIBOQS_COMMIT} && \
    git clone --progress --depth 1 --branch ${OPENSSL_BRANCH} ${OPENSSL_REPO} ${OPENSSL_SRC_PATH}

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

# A completed -new measurement must return success; error paths still return 1.
COPY s_time-new-exit.patch /opt/s_time-new-exit.patch
RUN git apply /opt/s_time-new-exit.patch && \
    make ${MAKE_DEFINES} && make install_sw

ARG CPU_PROFILING
RUN if [ "$CPU_PROFILING" = "True" ]; then \
    apt-get install -y linux-perf; fi

ENV OPENSSL "${OPENSSL_PATH}/bin/openssl"
ENV OPENSSL_CNF "${OPENSSL_PATH}/ssl/openssl.cnf"

WORKDIR /opt
COPY measurement-openssl-client.sh /opt/
COPY measurement-openssl-server.sh /opt/

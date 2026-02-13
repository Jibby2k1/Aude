FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake gcc g++ build-essential git \
    libfftw3-dev libconfig-dev libasound2-dev libpulse-dev \
    python3 python3-pip python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir numpy pyroomacoustics soundfile scipy

# Clone and build ODAS from upstream
RUN git clone https://github.com/introlab/odas.git /odas
WORKDIR /odas
RUN mkdir -p build && cd build && cmake .. && make -j$(nproc)

# Copy in our custom configs, test data, etc.
COPY test_data/ /odas/test_data/
COPY re6_sockets.cfg /odas/

FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source files
COPY CMakeLists.txt ./
COPY include/ ./include/
COPY src/ ./src/

# Build
RUN mkdir build && cd build && cmake .. && make

# Set environment variables (these should be overridden at runtime)
ENV GATE_API_KEY=""
ENV GATE_API_SECRET=""
ENV DRY_RUN="1"

# Run the application
CMD ["./build/depthos"]

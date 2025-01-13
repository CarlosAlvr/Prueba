# Use the official Rust image as a base
FROM rust:1.83 AS builder

# Set the working directory
WORKDIR /usr/src/communication-manager

# Copy the Cargo.toml and Cargo.lock files
COPY Cargo.toml Cargo.lock ./

# Copy the source code
COPY src ./src

# Build the application
RUN cargo build --release

# Use a minimal base image for the final container
FROM ubuntu:24.04

# Set the working directory
WORKDIR /usr/src/communication-manager

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the built binary from the builder stage
COPY --from=builder /usr/src/communication-manager/target/release/communication-manager .

# Copy the Python script
COPY acelerometro.py /usr/src/communication-manager/

# Run the Python script during the build
RUN python3 acelerometro.py

# Define environment variables
ENV PROCESS_ID="0001-0001"
ENV CONTROL_TOPIC_BASE="control/"
ENV TOPICS="user/process1/hello:simpleinput,simpleOutput:user/process1/hello2"


# Set the entrypoint
ENTRYPOINT ["./communication-manager"]
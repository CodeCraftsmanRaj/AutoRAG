FROM jenkins/jenkins:lts-jdk21

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install sonar-scanner
RUN curl -fsSL https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip \
    -o /tmp/sonar-scanner.zip && \
    apt-get update && apt-get install -y unzip && \
    unzip -q /tmp/sonar-scanner.zip -d /opt && \
    ln -s /opt/sonar-scanner-5.0.1.3006-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    rm /tmp/sonar-scanner.zip && \
    rm -rf /var/lib/apt/lists/*

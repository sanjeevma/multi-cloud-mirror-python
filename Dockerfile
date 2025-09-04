# Dockerfile
# Author: Sanjeev Maharjan <me@sanjeev.au>

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install crane
RUN CRANE_VERSION=$(curl -s https://api.github.com/repos/google/go-containerregistry/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    OS=$(uname -s | tr '[:upper:]' '[:lower:]') && \
    ARCH=$(uname -m | sed 's/x86_64/amd64/') && \
    curl -sL "https://github.com/google/go-containerregistry/releases/download/${CRANE_VERSION}/go-containerregistry_${OS}_${ARCH}.tar.gz" | tar xz crane && \
    mv crane /usr/local/bin/ && \
    chmod +x /usr/local/bin/crane

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Install Google Cloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install DigitalOcean CLI
RUN DOCTL_VERSION=$(curl -s https://api.github.com/repos/digitalocean/doctl/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    curl -sL "https://github.com/digitalocean/doctl/releases/download/${DOCTL_VERSION}/doctl-${DOCTL_VERSION#v}-linux-amd64.tar.gz" | tar xz && \
    mv doctl /usr/local/bin/ && \
    chmod +x /usr/local/bin/doctl

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY registries/ ./registries/
COPY utils/ ./utils/
COPY main.py .

# Copy configuration templates
COPY examples/ ./examples/
COPY config/ ./config/ 2>/dev/null || mkdir -p config

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "main.py", "--help"]

# Labels
LABEL org.opencontainers.image.title="Multi-Cloud Container Mirror"
LABEL org.opencontainers.image.description="Mirror container images across multiple cloud registries"
LABEL org.opencontainers.image.author="Sanjeev Maharjan <me@sanjeev.au>"
LABEL org.opencontainers.image.source="https://github.com/sanjeevma/multi-cloud-mirror-python"
LABEL org.opencontainers.image.version="1.0.0"

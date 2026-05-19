FROM python:3.12-slim

LABEL maintainer="Radio Shell"
LABEL description="Terminal FM Radio Player - Türkiye & Dünya"

# ffmpeg (ffplay içerir) + PulseAudio client yükle
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg pulseaudio-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy packaging files first to leverage Docker cache
COPY pyproject.toml .
COPY README.md .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir .

# Copy application source code
COPY src ./src

# Final installation of the package in editable-like fashion or just ensure it's there
RUN pip install --no-cache-dir .

# Favori ve özel istasyon verisi için volume
VOLUME ["/root/.radio-shell"]

# İnteraktif terminal gerekli
ENV TERM=xterm-256color
ENV PYTHONPATH=/app

ENTRYPOINT ["python3", "-m", "src.radio.main"]

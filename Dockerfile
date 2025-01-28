# Use Python 3.10 “slim” variant to keep the image small.
FROM python:3.10-slim

# Update & install dependencies for:
# 1) Headless Chrome (libgtk, libnss3, etc.)
# 2) Unzip for fetching Chrome driver
# 3) Fonts (sometimes needed by OCR or rendering)
# 4) Additional libraries often needed by PaddleOCR (like libgl1).
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm-dev \
    fonts-liberation \
    libgl1 \
    # If you notice other missing libs in logs, add them here
    && rm -rf /var/lib/apt/lists/*

# Create and switch to a working directory
WORKDIR /app

# Copy in your requirements file and install dependencies
COPY requirements.txt /app/

# Upgrade pip and install from requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN python scripts/setup_chrome.py

CMD ["python", "src/main.py"]

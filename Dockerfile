FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget unzip libnss3 libgtk-3-0 libx11-xcb1 libxcomposite1 \
    ...other-libs... \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Either rely on sys.path.insert(0, os.getcwd())
# OR set ENV PYTHONPATH=/app
RUN python scripts/setup_chrome.py

CMD ["python", "src/main.py"]

FROM python:3.9-slim

WORKDIR /app

# Installiere Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Erstelle Verzeichnisse
RUN mkdir -p /app/config /app/logs /app/rules

# Kopiere Anwendungsdateien
COPY src/ /app/src/
COPY config/ /app/config/
COPY run_server.py /app/

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV HOMEGROW_CONFIG=/app/config/config.yaml

# Starte den Server
CMD ["python", "-u", "/app/run_server.py"] 
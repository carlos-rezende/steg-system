FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY steg_system/ steg_system/
COPY README.md .

EXPOSE 8011

CMD ["uvicorn", "steg_system.web:app", "--host", "0.0.0.0", "--port", "8011"]

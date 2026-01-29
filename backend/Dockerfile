# backend/Dockerfile
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y buffer de stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 (driver de Postgres)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Comando por defecto (luego lo sobreescribe el compose, pero es buena práctica)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
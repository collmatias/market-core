FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (Postgres + gettext for i18n)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código (aunque esté vacío por ahora)
COPY . .

# Comando por defecto (producción usa gunicorn, dev usa docker-compose override con runserver)
CMD ["gunicorn", "marketcore.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
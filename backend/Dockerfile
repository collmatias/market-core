FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias de sistema (necesarias para Postgres)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código (aunque esté vacío por ahora)
COPY . .

# Comando por defecto
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
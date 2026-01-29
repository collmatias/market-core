#!/bin/bash

# Configuración
TIMESTAMP=$(date +"%Y-%m-%d_%H%M")
BACKUP_DIR="./backups"
CONTAINER_NAME="vetcore_db"
DB_USER="vetcore_user"

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Ejecutar pg_dump DENTRO del contenedor y guardar el archivo AFUERA
# Esto genera un archivo .sql comprimido (.gz) muy liviano y portable
docker exec -t $CONTAINER_NAME pg_dump -U $DB_USER vetcore_db | gzip > "$BACKUP_DIR/vetcore_backup_$TIMESTAMP.sql.gz"

# Limpieza: Borrar backups mayores a 30 días
find $BACKUP_DIR -type f -name "*.gz" -mtime +30 -delete

echo "Backup generado: $BACKUP_DIR/vetcore_backup_$TIMESTAMP.sql.gz"
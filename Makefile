# --- Variables ---
COMPOSE = docker compose
API_CONTAINER = api

# --- Ayuda (Default) ---
help:
	@echo "🛠️  Comandos de VetCore:"
	@echo "  make up          : Levanta el proyecto (y reconstruye si es necesario)"
	@echo "  make down        : Baja los contenedores"
	@echo "  make logs        : Ver logs en tiempo real"
	@echo "  make db          : Crea migraciones y migra la base de datos (todo en uno)"
	@echo "  make superuser   : Crea un admin de Django"
	@echo "  make shell       : Entra a la consola de Python/Django"
	@echo "  make bash        : Entra a la terminal del contenedor"
	@echo "  make perms       : Arregla permisos de archivos en Linux (sudo)"

# --- Comandos Docker ---
up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

# --- Comandos Django / Base de Datos ---
migrations:
	$(COMPOSE) exec $(API_CONTAINER) python manage.py makemigrations

migrate:
	$(COMPOSE) exec $(API_CONTAINER) python manage.py migrate

# Este corre los dos anteriores juntos
db: migrations migrate
	@echo "✅ Base de datos actualizada."

superuser:
	$(COMPOSE) exec $(API_CONTAINER) python manage.py createsuperuser

shell:
	$(COMPOSE) exec $(API_CONTAINER) python manage.py shell

# Entrar a la terminal del container por si necesitas explorar
bash:
	$(COMPOSE) exec $(API_CONTAINER) /bin/bash

# --- Utilidades Linux ---
# Este es vital cuando Docker crea archivos como root y no puedes editarlos
perms:
	sudo chown -R $$USER:$$USER backend/
	@echo "✅ Permisos corregidos."

# --- Testing ---
test:
	$(COMPOSE) exec $(API_CONTAINER) python manage.py test
# ==============================================================================
# Dockerfile para Backend (Django + Django REST Framework)
# Panadería Santiago — SI-1
# ==============================================================================

FROM python:3.12-slim

# Evita que Python escriba archivos .pyc y fuerza salida sin buffer para ver logs inmediatamente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependencias del sistema necesarias para PostgreSQL y utilitarios
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copia e instala dependencias de Python primero (aprovecha la caché de capas de Docker)
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del backend
COPY . /app/

# Expone el puerto del backend Django
EXPOSE 8000

# Comando por defecto para desarrollo local
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

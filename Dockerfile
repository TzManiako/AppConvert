FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Configurar variables de entorno
ENV PORT=8080
ENV HOST=0.0.0.0

# Exponer el puerto
EXPOSE 8080

# Comando para iniciar la aplicación con gunicorn
CMD gunicorn --bind $HOST:$PORT app:app
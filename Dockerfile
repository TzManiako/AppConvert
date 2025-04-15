# Dockerfile

# 1. Usar una imagen base oficial de Python
# Usamos 'slim' para una imagen más ligera. 'bullseye' especifica la versión de Debian.
FROM python:3.10-slim-bullseye

# 2. Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1  # Evita que Python escriba archivos .pyc
ENV PYTHONUNBUFFERED 1      # Muestra los logs de Python inmediatamente

# 3. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Instalar dependencias del sistema (¡Aquí es donde añadirías LibreOffice si fuera necesario!)
# Descomenta y adapta la siguiente línea si necesitas instalar paquetes de sistema:
# RUN apt-get update && apt-get install -y --no-install-recommends paquete1 paquete2 && apt-get clean && rm -rf /var/lib/apt/lists/*
# Ejemplo para LibreOffice (puede aumentar significativamente el tamaño de la imagen y el tiempo de build):
# RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. Instalar dependencias de Python
# Copia solo el archivo de requerimientos primero para aprovechar el caché de Docker
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el código de tu aplicación al contenedor
COPY . .

# 7. Exponer el puerto en el que correrá Gunicorn/Flask
# Render inyectará la variable de entorno PORT. Gunicorn debe usarla.
# No necesitas EXPOSE aquí necesariamente ya que Render gestiona el mapeo, pero es buena práctica documentarlo.
# EXPOSE 8000 # (El valor real será el de la variable $PORT de Render)

# 8. Comando para ejecutar la aplicación usando un servidor WSGI (Gunicorn)
# Escuchará en todas las interfaces (0.0.0.0) y en el puerto que Render asigne ($PORT)
# Ajusta 'app:app' si tu archivo principal o instancia Flask se llama diferente.
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
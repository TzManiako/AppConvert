#!/usr/bin/env bash
# Actualizar e instalar LibreOffice
apt-get update
apt-get install -y libreoffice

# Verificar la instalación
if which libreoffice > /dev/null; then
  echo "LibreOffice instalado correctamente"
else
  echo "Error: LibreOffice no está instalado correctamente"
  # Intenta con soffice
  if which soffice > /dev/null; then
    echo "Pero soffice está disponible"
  else
    echo "Error: soffice tampoco está disponible"
  fi
fi

# Instalar dependencias de Python
pip install -r requirements.txt
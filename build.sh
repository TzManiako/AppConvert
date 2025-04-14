#!/usr/bin/env bash
# Actualizar e instalar dependencias
apt-get update
apt-get install -y libreoffice unoconv pandoc texlive-latex-base

# Verificar la instalación
which libreoffice || echo "LibreOffice no está instalado correctamente"
which unoconv || echo "unoconv no está instalado correctamente"
which pandoc || echo "pandoc no está instalado correctamente"

# Instalar dependencias de Python
pip install -r requirements.txt
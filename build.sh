#!/usr/bin/env bash
# Instalar dependencias del sistema
apt-get update
apt-get install -y libreoffice

# Instalar dependencias de Python
pip install -r requirements.txt
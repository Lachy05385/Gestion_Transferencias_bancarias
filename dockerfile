FROM python:3.11-slim

# Instalar Tesseract (esto SÍ funciona en Docker)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para iniciar la aplicación
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
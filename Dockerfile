# Usamos una versión slim de Python para que la imagen sea liviana
FROM python:3.14-slim

# Evitamos que Python guarde en buffer la salida de consola (logs inmediatos en GCP)
ENV PYTHONUNBUFFERED=1

# Instalamos dependencias del sistema necesarias para que Playwright/Chromium funcione
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpangocairo-1.0-0 libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Definimos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero el archivo de requisitos e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalamos Chromium Y TODAS sus dependencias de sistema oficial en una sola capa
RUN playwright install --with-deps chromium

# Copiamos el resto de tu código al contenedor
COPY . .

# Comando por defecto al ejecutar el contenedor
CMD ["python", "scraper.py"]
# Używamy pełnego obrazu Pythona
FROM python:3.11

# Ustawienia Pythona
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Katalog roboczy
WORKDIR /app

# Instalacja zależności
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Skopiuj resztę projektu
COPY . /app

# Uruchom Flaska (Railway poda zmienną $PORT)
CMD ["python", "app.py"]

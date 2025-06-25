FROM python:3.12

# zapobiegnij tworzeniu .pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/app

# skopiuj wymagania i zainstaluj
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# skopiuj resztę repo w osobnym kroku (lepszy caching)
COPY . .

# domyślny port we Flask
EXPOSE 5000

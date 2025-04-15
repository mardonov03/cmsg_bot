FROM python:3.11-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY . .

# Переменные окружения
ENV DB_USER=postgres
ENV DB_PASSWORD=dexqon.uz.com.1
ENV DB_NAME=cmsg
ENV DB_HOST=127.0.0.1
ENV PYTHONUNBUFFERED=1

# Проверка структуры проекта
RUN find . > structure.txt

# Запуск проекта через модуль
CMD ["python3", "-m", "tgbot.main"]

FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директории для БД
RUN mkdir -p /data

# Переменные окружения по умолчанию
ENV DB_PATH=/data/chicken.db

# Запуск бота
CMD ["python", "main.py"]

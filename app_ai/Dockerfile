FROM python:3.10-slim

WORKDIR /app

# Копируем только requirements.txt сначала
COPY requirements.txt .

# Устанавливаем зависимости (этот слой закэшируется)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

RUN mkdir -p logs

# Открытие порта для Gradio
EXPOSE 7860

# Запуск приложения
CMD ["python", "app.py"]

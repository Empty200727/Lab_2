# Образ с Python 3.12
FROM python:3.12-slim

# Рабочая папка внутри контейнера
WORKDIR /app

# Сначала ставим библиотеки (слой кешируется, пока не изменится requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код программы
COPY . .

# Папки для БД и отчётов (монтируются как volume, чтобы файлы остались на компьютере)
RUN mkdir -p /app/data /app/reports
VOLUME ["/app/data", "/app/reports"]

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]

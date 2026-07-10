FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ADS_MYSQL_HOST=mysql \
    ADS_MYSQL_PORT=3306 \
    ADS_MYSQL_DATABASE=ecommerce_ads \
    ADS_MYSQL_USER=ecommerce \
    ADS_MYSQL_PASSWORD=ecommerce_password

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

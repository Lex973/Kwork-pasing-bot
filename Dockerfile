FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY kwork_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium --with-deps

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "kwork_bot.bot"]

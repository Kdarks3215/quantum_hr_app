FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk update \
    && apk upgrade --no-cache \
    && apk add --no-cache build-base libffi-dev postgresql-dev \
    && addgroup -S app && adduser -S app -G app \
    && mkdir -p instance

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh && chown -R app:app /app

USER app

ENV SEED_DEFAULT_DATA=false

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

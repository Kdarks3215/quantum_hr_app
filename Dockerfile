FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk update \
    && apk upgrade --no-cache \
    && apk add --no-cache build-base libffi-dev \
    && mkdir -p instance

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    SEED_DEFAULT_DATA=true

EXPOSE 5000

CMD ["flask", "run"]

FROM python:3.9

WORKDIR /app

ENV PYTHONBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

CMD ["gunicorn", "--bind 0.0.0.0:8080", "src.api:app"]


FROM python:3.12.3-slim

WORKDIR /code

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 9000

ENTRYPOINT ["gunicorn", "app:app"]

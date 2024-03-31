# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster
EXPOSE 8000

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install --upgrade pip

COPY app.py .
COPY rnn.py .
COPY common_functions.py .
COPY default_config.yaml .
COPY regressor_model.keras .
COPY scaler.pkl .
COPY groceries.csv .
COPY groceries_bread_1.csv .
COPY groceries_bread_2.csv .

CMD python app.py

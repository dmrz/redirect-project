FROM python:3.12-slim
RUN apt update
RUN apt install -y build-essential
COPY . /app
WORKDIR /app

RUN pip install -U pip
RUN pip install --prefer-binary -e .

CMD python hello/server.py

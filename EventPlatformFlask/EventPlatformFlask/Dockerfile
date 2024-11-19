FROM ubuntu:focal
WORKDIR /app
RUN apt-get update -y && apt-get install -y python3-pip python3-dev build-essential libssl-dev

# Flask-app requirements
COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r ./requirements.txt

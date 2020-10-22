FROM python:buster

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
RUN apt-get update && \
        apt-get install -y libffi-dev libnacl-dev python3-dev

ENTRYPOINT [ "python3", "src/hanna_support.py" ]

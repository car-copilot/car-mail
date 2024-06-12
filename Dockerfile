FROM python:latest

WORKDIR /app

COPY app/requirements.txt ./

RUN pip install -r requirements.txt

COPY app/main.py ./

CMD [ "python3", "-u", "./main.py"]

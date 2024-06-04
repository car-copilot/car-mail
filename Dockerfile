FROM python:latest

WORKDIR /app

COPY app/requirements.txt ./
COPY app/main.py ./

RUN pip install -r requirements.txt

CMD [ "python3", "-u", "./main.py"]
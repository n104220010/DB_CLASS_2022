FROM python:3.7.2-stretch

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

RUN python -m pip install cx_Oracle --upgrade --user

RUN unzip instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip

RUN sudo apt install libaio1

ENV FLASK_APP=app.py

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

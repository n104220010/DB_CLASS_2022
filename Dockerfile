FROM python:3.7.2-stretch

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

RUN python -m pip install cx_Oracle --upgrade --user

RUN mkdir -p /opt/oracle

RUN unzip instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip -d /opt/oracle

RUN ls /opt/oracle

RUN apt-get -y update

RUN apt-get -y install libaio1

RUN sh -c "echo /opt/oracle/instantclient_21_5 > /etc/ld.so.conf.d/oracle-instantclient.conf"

RUN ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_5:$LD_LIBRARY_PATH

ENV FLASK_APP=app.py

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

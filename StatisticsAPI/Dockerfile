FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get install -y --no-install-recommends libatlas-base-dev gfortran nginx supervisor

RUN pip3 install uwsgi
RUN pip3 install setuptools==65.5.1

COPY requirements.txt ./requirements.txt

COPY config/nginx.conf /etc/nginx/
RUN useradd --no-create-home nginx
RUN rm /etc/nginx/sites-enabled/default
RUN rm -r /root/.cache
COPY config/flask_nginx.conf /etc/nginx/conf.d/

COPY config/uwsgi.ini /etc/uwsgi/
COPY config/supervisord.conf /etc/supervisor/

RUN python3.8 -m pip install -r requirements.txt
RUN pip3 install urllib3==1.26.5

COPY src /project/src
COPY config /project/config

WORKDIR /project
CMD ["/usr/bin/supervisord"]
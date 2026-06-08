ARG python_version=3.9.7

FROM python:$python_version
ENV TG_UP_CONFIG_DIRECTORY=/config
ENV PYTHONPATH=/app/
VOLUME /config
VOLUME /files

RUN mkdir /app
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
COPY tg_up/ /app/tg_up/
WORKDIR /files

ENTRYPOINT ["/usr/local/bin/python", "/app/tg_up/management.py"]

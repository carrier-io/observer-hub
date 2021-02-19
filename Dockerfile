FROM python:3.7-alpine

RUN apk add build-base libffi-dev openssl-dev
RUN apk add --no-cache ffmpeg

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
ADD MANIFEST.in /tmp/MANIFEST.in

ADD setup.py /tmp/setup.py
ADD requirements.txt /tmp/requirements.txt
COPY observer_hub /tmp/observer_hub
RUN pip install git+https://github.com/carrier-io/arbiter.git
RUN cd /tmp && python setup.py install && rm -rf /tmp/*

WORKDIR /tmp
SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["app"]
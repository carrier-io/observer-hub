FROM python:3.7-alpine

RUN apk add build-base libffi-dev openssl-dev

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

ADD setup.py /tmp/setup.py
ADD requirements.txt /tmp/requirements.txt
COPY browser_hub /tmp/browser_hub
RUN cd /tmp && python setup.py install && rm -rf /tmp/*

ENTRYPOINT ["app"]
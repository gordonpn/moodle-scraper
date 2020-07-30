FROM python:3.8-alpine

RUN adduser \
    --disabled-password \
    --home /home/appuser \
    --shell /bin/bash \
    --system \
    --uid 1000 \
    appuser

RUN apk update && apk --no-cache add \
    ca-certificates \
    libreoffice \
    libreoffice-base \
    libreoffice-lang-en_us

RUN update-ca-certificates

RUN apk --no-cache add --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community \
    openjdk11

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN mkdir --verbose /home/appuser/courses
RUN chown appuser /home/appuser
RUN chown appuser /home/appuser/courses

WORKDIR /home/appuser
USER appuser

COPY . .

VOLUME ["/home/appuser/courses"]

CMD ["python", "./main.py"]

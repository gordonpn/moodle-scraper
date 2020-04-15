FROM ubuntu:eoan

RUN apt update && add-apt-repository -y ppa:deadsnakes/ppa
RUN apt update && apt install -y \
  libreoffice \
  python3.8 \
  python3.8-distutils \
  software-properties-common

RUN python3.8 -m pip install --upgrade pip setuptools wheel

COPY requirements.txt /tmp/
RUN python3.8 -m pip install -r /tmp/requirements.txt

RUN useradd -rm -d /home/appuser -s /bin/bash -u 1000 appuser
WORKDIR /home/appuser
USER appuser

RUN mkdir -p courses

COPY . .

VOLUME ["/home/appuser/courses"]

CMD ["python3.8", "./moodle_scraper.py --automated --convert"]

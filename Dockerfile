FROM ubuntu:eoan

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt upgrade -y
RUN apt install -y \
  build-essential \
  curl \
  git \
  libbz2-dev \
  libffi-dev \
  liblzma-dev \
  libncurses5-dev \
  libncursesw5-dev \
  libreadline-dev \
  libreoffice \
  libsqlite3-dev \
  libssl-dev \
  llvm \
  make \
  python-openssl \
  tk-dev \
  wget \
  xz-utils \
  zlib1g-dev

RUN ln -fs /usr/share/zoneinfo/America/Montreal /etc/localtime
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN git clone https://github.com/pyenv/pyenv.git /home/appuser/.pyenv

ENV PYENV_ROOT="/home/appuser/.pyenv"
ENV PATH="${PYENV_ROOT}/bin:${PATH}"

#RUN /bin/bash -c source /home/appuser/.profile

RUN pyenv install 3.8.2

RUN pip3 install --upgrade pip
RUN pip install --upgrade setuptools wheel

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN useradd -rm -d /home/appuser -s /bin/bash -u 1000 appuser
WORKDIR /home/appuser
USER appuser

RUN mkdir -p courses

COPY . .

VOLUME ["/home/appuser/courses"]

CMD ["python", "./moodle_scraper.py --automated --convert"]

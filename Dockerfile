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

RUN git clone https://github.com/pyenv/pyenv.git ~/.pyenv

RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
RUN echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile

RUN source ~/.profile

RUN pyenv install 3.8.2

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

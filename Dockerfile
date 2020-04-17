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

RUN useradd --home-dir /home/appuser --system --shell /bin/bash --uid 1000 appuser

RUN git clone https://github.com/pyenv/pyenv.git /home/appuser/.pyenv

ENV PYENV_ROOT="/home/appuser/.pyenv"
ENV PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"

RUN pyenv install 3.8.2

RUN pyenv global 3.8.2

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools wheel

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN mkdir --verbose /home/appuser/courses
RUN chown appuser /home/appuser
RUN chown appuser /home/appuser/courses

WORKDIR /home/appuser
USER appuser

COPY . .

VOLUME ["/home/appuser/courses"]

CMD ["python", "./moodle_scraper.py"]

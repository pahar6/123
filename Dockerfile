FROM ghcr.io/withlogicco/poetry:1.4.0-python-3.11-buster
WORKDIR /tmp
RUN apt update \
#    && apt install -y --no-install-recommends gcc libc6-dev \
    && apt clean -y \
    && rm -rf /var/lib/apt/* /var/log/* /var/cache/*

WORKDIR /app
COPY pyproject.toml ./
RUN poetry config installer.max-workers 2
RUN poetry install --no-root
COPY chat_scanner chat_scanner
RUN pip freeze
COPY README.md README.md
ENV PYTHONPATH=/app
#  Запустить poetry install до копирования файлов

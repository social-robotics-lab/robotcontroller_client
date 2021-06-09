FROM python:3.8-slim

RUN useradd -m -d /home/sota -s /bin/bash sota
USER sota
WORKDIR /tmp
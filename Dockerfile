FROM ubuntu

WORKDIR /workspace

# OpenJTalk
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    ffmpeg \
    hts-voice-nitech-jp-atr503-m001 \
    open-jtalk \
    open-jtalk-mecab-naist-jdic \
    python3-pip \
    unzip \
    wget
    
RUN wget --no-check-certificate http://sourceforge.net/projects/mmdagent/files/MMDAgent_Example/MMDAgent_Example-1.8/MMDAgent_Example-1.8.zip \
    && unzip MMDAgent_Example-1.8.zip \
    && cp -r MMDAgent_Example-1.8/Voice/mei/ /usr/share/hts-voice/ \
    && rm -rf MMDAgent_Example-1.8.zip MMDAgent_Example-1.8

RUN pip3 install pydub

# RUN useradd -m -d /home/sota -s /bin/bash sota
# USER sota
WORKDIR /tmp
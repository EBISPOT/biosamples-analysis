FROM python:2.7

RUN \
     apt-get update && \
     apt-get install gawk && \
     apt-get clean && \
     pip install requests

COPY app.py /
COPY args.txt /
COPY file.csv /
COPY run.sh /

ENTRYPOINT ["./run.sh"]

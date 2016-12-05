FROM python:3.5-alpine

RUN ["pip", "install", "requests", "unicodecsv", "futures"]

COPY collateontologies.py /
COPY entrypoint.sh /

ENTRYPOINT ["sh", "entrypoint.sh"]

FROM python:2.7-alpine

RUN ["pip", "install", "requests", "unicodecsv", "futures", "requests-futures"]

COPY collate-ontologies.py /
COPY entrypoint.sh /

ENTRYPOINT ["sh", "entrypoint.sh"]

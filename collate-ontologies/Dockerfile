FROM python:2.7-alpine

COPY collate-ontologies.py /
RUN ["pip", "install", "requests", "unicodecsv"]

COPY entrypoint.sh /

ENTRYPOINT ["sh", "entrypoint.sh"]

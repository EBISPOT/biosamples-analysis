FROM python:2.7-alpine

COPY collate-efo.py /
RUN ["pip", "install", "requests", "unicodecsv"]

ENTRYPOINT ["python", "-u", "/collate-efo.py"]

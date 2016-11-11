FROM python:2.7-alpine

COPY collate-attributes.py /
RUN ["pip", "install", "requests", "unicodecsv", "inflection"]

ENTRYPOINT ["python", "/collate-attributes.py"]

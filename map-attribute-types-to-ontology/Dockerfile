FROM python:2.7-alpine

COPY map-attribute-types.py /
RUN ["pip", "install", "requests", "unicodecsv", "inflection"]

ENTRYPOINT ["python", "/map-attribute-types.py"]

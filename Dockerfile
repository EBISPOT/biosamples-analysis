FROM python:2.7-alpine

COPY build_csv.py /
RUN ["pip", "install", "requests", "unicodecsv", "inflection"]

ENTRYPOINT ["python", "/collate-attributes.py"]

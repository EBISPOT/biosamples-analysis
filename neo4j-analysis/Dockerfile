FROM python:2.7

COPY neo4j-analysis.py /
RUN ["pip", "install", "neo4j-driver", "wordcloud", "matplotlib", "pillow", "image"]

ENTRYPOINT ["python", "/neo4j-analysis.py"]

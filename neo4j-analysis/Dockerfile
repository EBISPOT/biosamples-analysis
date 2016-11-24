FROM python:2.7

RUN ["pip", "install", "neo4j-driver", "wordcloud", "matplotlib", "pillow", "image"]

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /
RUN chmod +x /wait-for-it.sh

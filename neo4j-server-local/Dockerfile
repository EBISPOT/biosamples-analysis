FROM neo4j:3.0.6

ENV NEO4J_HOME /var/lib/neo4j
ENV NEO4J_AUTH none
ENV APOC_URI "https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/3.0.4.1/apoc-3.0.4.1-all.jar"

RUN curl --show-error --location --output $NEO4J_HOME/plugins/apoc-3.0.4.1-all.jar $APOC_URI 
EXPOSE 7474 7473 7687

CMD ["neo4j"]

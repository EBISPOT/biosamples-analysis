FROM neo4j:3.0.6

COPY load.sh /
COPY indexes.cypher /

ENTRYPOINT ["/load.sh"]

# biosamples-analysis
Contains python scripts and cypher to read BioSamples info from Solr, store in Neo4J database

Docker
======

Dockerfile constains ths instructions to build a docker container that will query Solr
and build the csv files when run.

docker-compose contains docker-compose instructions for that container, and for a neo4j instance

docker-compose run biosamples-metrics

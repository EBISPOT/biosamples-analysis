# biosamples-analysis
Contains python scripts and cypher to read BioSamples info from Solr, store in Neo4J database

Docker
======


The plan is to have 4 different docker containers:
	collate-attributes to query Solr and create a single combined CSV
	create-csv to split that combined CSV into separate ones
	build-neo to use the neo4j bulk loader to create a graph database
	neo-data to have a self-contained neo4j server with data inside

docker-compose run collate-attributes
docker-compose run create-csv

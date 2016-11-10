#!/usr/bin/env bash

# Read environmental config from here...
source "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"/load_env.sh

# Clean any existing content
echo "Removing any existing content at $NEO_DATA/graph.db.tmp"
rm -rf "$NEO_DATA"/graph.db.tmp

# Create the new content
echo "Creating new database..."
time nice "$NEO4J_BIN"/neo4j-import --bad-tolerance 10000 --into "$NEO_DATA"/graph.db.tmp --i-type string \
        --nodes:Sample "./output/samples.csv" \
        --nodes:Attributes "./output/attributes.csv" \
        --nodes:AttributeType "./output/types.csv" \
        --nodes:AttributeValue "./output/values.csv" \
        --nodes:OntologyTerm "./output/ontologies.csv" \
        --relationships:has_attribute "./output/has_attribute.csv" \
        --relationships:has_value "./output/has_value.csv" \
        --relationships:has_type "./output/has_type.csv" \
        --relationships:has_iri "./output/has_iri.csv"

# Create indexes
#echo "Creating indexes..."
#time nice "$NEO4J_BIN"/neo4j-shell -path "$NEO_DATA"/graph.db.tmp -file ./indexes.cypher

# Replace graph
rm -rf "$NEO_DATA"/graph.db
mv "$NEO_DATA"/graph.db.tmp "$NEO_DATA"/graph.db

echo "All Done!"

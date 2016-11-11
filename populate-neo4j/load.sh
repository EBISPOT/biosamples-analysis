#!/usr/bin/env bash

NEO4J_BIN=/var/lib/neo4j/bin
NEO4J_DATA=/output

# Clean any existing content
echo "Removing any existing content at $NEO4J_DATA/graph.db.tmp"
rm -rf "$NEO4J_DATA"/graph.db.tmp

# Create the new content
echo "Creating new database..."
time nice "$NEO4J_BIN"/neo4j-import --bad-tolerance 10000 --into "$NEO4J_DATA/graph.db.tmp" --i-type string \
        --nodes:Sample "$NEO4J_DATA/samples.csv" \
        --nodes:Attributes "$NEO4J_DATA/attributes.csv" \
        --nodes:AttributeType "$NEO4J_DATA/types.csv" \
        --nodes:AttributeValue "$NEO4J_DATA/values.csv" \
        --nodes:OntologyTerm "$NEO4J_DATA/ontologies.csv" \
        --relationships:has_attribute "$NEO4J_DATA/has_attribute.csv" \
        --relationships:has_value "$NEO4J_DATA/has_value.csv" \
        --relationships:has_type "$NEO4J_DATA/has_type.csv" \
        --relationships:has_iri "$NEO4J_DATA/has_iri.csv"

# Create indexes
#echo "Creating indexes..."
#time nice "$NEO4J_BIN"/neo4j-shell -path $NEO4J_DATA/graph.db.tmp -file ./indexes.cypher

# Replace graph
rm -rf "$NEO4J_DATA/graph.db"
mv "$NEO4J_DATA/graph.db.tmp" "$NEO4J_DATA/graph.db"

echo "All Done!"

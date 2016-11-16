# Cypher queries for BioSamples Attribute Analysis

## Queries

### get the number of samples

~~~
MATCH (s:Sample), (a:Attribute), (t:AttributeType), (v:AttributeValue), (o:OntologyTerm) RETURN count(s), count(a), count(t), count(v), count(o)
~~~


### Get most frequently used attributes

The following query extracts the top 100 mostly commonly used attribute type/value pairs and counts their usage.

~~~~
MATCH (a:Attribute)<-[:hasAttribute]-(s:Sample) WITH a, COUNT(s) AS usage_count RETURN a.type, a.value, usage_count ORDER BY usage_count DESC LIMIT 100
~~~~

### Get a list of attribute values where attribute type is "Disease State"

~~~~
MATCH (at:AttributeType {name: "Disease State"})<-[:hasType]-(a:Attribute)-[:hasValue]->(av:AttributeValue) RETURN av.name
~~~~

### Get a list of attribute values where attribute type is "Disease State" with counts

~~~~
MATCH (at:AttributeType {name: "Disease State"})<-[:hasType]-(a:Attribute)-[:hasValue]->(av:AttributeValue) WITH a, av MATCH (s:Sample)-[:hasAttribute]->(a)-[:hasValue]->(av) WITH av, COUNT(s) AS usage_count RETURN av.name, usage_count ORDER BY usage_count DESC
~~~~

### Get a list of attribute values which have more than one attribute type, sorted by most frequently used

~~~~
MATCH (av:AttributeValue)<-[:hasValue]-(:Attribute)-[:hasType]->(at:AttributeType) WITH av, COUNT(at) AS num_of_types WHERE num_of_types > 1 MATCH (s:Sample)-[:hasAttribute]->(a:Attribute)-[:hasValue]->(av) WITH av, COUNT(s) AS usage_count RETURN av ORDER BY usage_count DESC LIMIT 10
~~~~

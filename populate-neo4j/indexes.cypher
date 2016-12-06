CREATE CONSTRAINT ON (sample:Sample) ASSERT sample.accession IS UNIQUE;
CREATE CONSTRAINT ON (ot:OntologyTerm) ASSERT ot.iri IS UNIQUE;
CREATE CONSTRAINT ON (attr:Attribute) ASSERT attr.attributeId IS UNIQUE;
CREATE CONSTRAINT ON (type:AttributeType) ASSERT type.name IS UNIQUE;
CREATE CONSTRAINT ON (value:AttributeValue) ASSERT value.name IS UNIQUE;
CREATE CONSTRAINT ON (eot:efoOntologyTerm) ASSERT eot.iri IS UNIQUE;
CREATE CONSTRAINT ON (eot:ncbitaxonOntologyTerm) ASSERT eot.iri IS UNIQUE;

CREATE INDEX on :Attribute(type);
CREATE INDEX on :Attribute(value);
CREATE INDEX on :Attribute(iri);
CREATE INDEX on :efoOntologyTerm(label);
CREATE INDEX on :efoOntologyTerm(obselete);
CREATE INDEX on :ncbitaxonOntologyTerm(label);
CREATE INDEX on :ncbitaxonOntologyTerm(obselete);

MATCH (o:OntologyTerm),(e:efoOntologyTerm) WHERE o.iri = e.iri CREATE (o)-[r:inEfo]->(e);
MATCH (o:OntologyTerm),(e:ncbitaxonOntologyTerm) WHERE o.iri = e.iri CREATE (o)-[r:inNcbitaxon]->(e);

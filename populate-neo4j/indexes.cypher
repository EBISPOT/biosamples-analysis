CREATE CONSTRAINT ON (sample:Sample) ASSERT sample.accession IS UNIQUE;
CREATE CONSTRAINT ON (ot:OntologyTerm) ASSERT ot.iri IS UNIQUE;
CREATE CONSTRAINT ON (attr:Attribute) ASSERT attr.attributeId IS UNIQUE;
CREATE CONSTRAINT ON (type:AttributeType) ASSERT type.name IS UNIQUE;
CREATE CONSTRAINT ON (value:AttributeValue) ASSERT value.name IS UNIQUE;
CREATE CONSTRAINT ON (eot:EfoOntologyTerm) ASSERT eot.iri IS UNIQUE;

CREATE INDEX on :Attribute(type);
CREATE INDEX on :Attribute(value);
CREATE INDEX on :Attribute(iri);

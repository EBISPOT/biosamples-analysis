CREATE CONSTRAINT ON (sample:Sample) ASSERT sample.accession IS UNIQUE;
CREATE CONSTRAINT ON (ot:OntologyTerm) ASSERT ot.iri IS UNIQUE

CREATE INDEX on :Attribute(type)
CREATE INDEX on :Attribute(value)

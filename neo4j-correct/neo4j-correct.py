# pip install neo4j-driver wordcloud matplotlib pillow image
import argparse
import csv
import os
import random
from neo4j.v1 import GraphDatabase, basic_auth

import re


def get_most_common_attributes(db_driver, n_attributes, force=True):
	attr_types = []
	if n_attributes == 0:
		return attr_types
	else:
		if not force and os.path.isfile('neo4j-analysis/csv/attr_common.csv'):
			with open('neo4j-analysis/csv/attr_common.csv', 'r') as f:
				attr_re = re.compile("(?P<type>(?:\w+\s?)+)\s\((?P<usage_count>\d+)\)")
				csv_reader = csv.reader(f)
				n = 0
				while n < n_attributes:
					row = next(csv_reader)
					value = row[0]
					result = attr_re.match(value)
					attr_types.append((str(result.group('type')), int(result.group('usage_count'))))
					n += 1
		else:
			print 'Querying database for the %d most common attribute types' % n_attributes
			with db_driver.session() as session:
				results = session.run("MATCH (:Sample)-[u:hasAttribute]->(a:Attribute) "
				                      "RETURN a.type AS type, COUNT(u) AS usage_count "
				                      "ORDER BY usage_count DESC "
				                      "LIMIT {n_attributes}", {"n_attributes": n_attributes})
				for result in results:
					attr_types.append((result["type"], result["usage_count"]))
		return attr_types


def correct_obsolete_terms(db_driver):
	print "Updating obsolete ontology terms for Sex and Organism Part attributes"
	correcting_map = {
		"http://www.ebi.ac.uk/efo/EFO_0001266": "http://purl.obolibrary.org/obo/PATO_0000384",  # male
		"http://www.ebi.ac.uk/efo/EFO_0001265": "http://purl.obolibrary.org/obo/PATO_0000383",  # female
		"http://www.ebi.ac.uk/efo/EFO_0000887": "http://purl.obolibrary.org/obo/UBERON_0002107",  # liver
		"http://www.ebi.ac.uk/efo/EFO_0000296": "http://purl.obolibrary.org/obo/UBERON_0000178",  # blood
		"http://www.ebi.ac.uk/efo/EFO_0000854": "http://purl.obolibrary.org/obo/UBERON_0001911",  # mammary gland
		"http://www.ebi.ac.uk/efo/EFO_0000868": "http://purl.obolibrary.org/obo/UBERON_0002371",  # bone marrow
		"http://www.ebi.ac.uk/efo/EFO_0000993": "http://purl.obolibrary.org/obo/PO_0025034"  # leaf
	}

	with db_driver.session() as session:
		for (obsolete_iri, correct_iri) in correcting_map.items():
			cypher = \
				"MATCH (a:Attribute)-[r:hasIri]->(o_old:OntologyTerm{iri:{obsolete_iri}}), " \
				"(o_new:OntologyTerm{iri:{correct_iri}}) "\
				"CREATE (a)-[:hasIri]->(o_new)" \
				"DELETE r"
			session.run(cypher, {"obsolete_iri": obsolete_iri, "correct_iri": correct_iri})


def correct_numeric_organism(db_driver):
	with db_driver.session() as session:
		cypher = \
			"MATCH (a:Attribute{type:'Organism'})-[:hasIri]->(o:OntologyTerm)-[:inEfo]->(efo:EfoOntologyTerm) " \
			"WITH a, a.value as value, o.iri as iri, '\\b(.+)_' + a.value + '\\b' AS regex, efo "\
			"WHERE value =~ '[0-9]+' AND iri =~ regex " \
			"SET a.value = efo.label"
		session.run(cypher)

if __name__ == "__main__":
	print "Welcome to the BioSamples analysis"

parser = argparse.ArgumentParser()
parser.add_argument('--hostname', default="neo4j-server-local")

args = parser.parse_args()

driver = GraphDatabase.driver("bolt://" + args.hostname)

print "Applying database corrections"

correct_obsolete_terms(driver)
correct_numeric_organism(driver)


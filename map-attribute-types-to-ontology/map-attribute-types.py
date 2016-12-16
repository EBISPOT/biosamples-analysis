import os
import argparse

import requests
import unicodecsv
import json
# import concurrent.futures
from neo4j.v1 import GraphDatabase, basic_auth


class Mapping:
	def __init__(self, value, label, iri, confidence, curated=False):
		self.value = value
		self.label = label
		self.iri = iri
		self.confidence = confidence
		self.curated = curated

	def __str__(self):
		try:
			return "Mapping:\{value={value:s},label={label:s}," \
			       "iri={iri:s},confidence={confidence:s},curated={curated:%s}\}".format(
				value=self.value, label=self.label, iri=self.iri,
				confidence=self.confidence.upper(), curated=self.curated)
		except UnicodeDecodeError:
			print "Something went wrong handling mapping for " + self.value


def get_most_common_attribute_types(db_driver, n_attributes):
	attr_types = []
	if n_attributes == 0:
		return attr_types
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


def get_curated_annotation(value, datasource=None):
	pass


def get_ols_annotation(value, ontology=None):
	url = "http://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate?" \
	      "propertyValue={value:s}&" \
	      "filter=required:[none]&" \
	      "filter=ontologies:[{ontology:s}]".format(value=value, ontology=ontology)
	response = requests.get(url)
	mapping = None
	if response.status_code == 200:
		resource = json.loads(response.content)
		if resource:
			result = resource[0]
			mapping = Mapping(value, result.annotadedProperty.propertyValue,
							  result.semanticTags[0], result.confidence, False)
	return mapping

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--ontology", "-o", type=str, default="all")
	parser.add_argument("--darasource", "-ds", type=str, default="all")
	parser.add_argument("--hostname", default="neo4j-server-local")
	parser.add_argument("--attr_number", "-n", type=int, default=100)
	args = parser.parse_args()

	driver = GraphDatabase.driver("bolt://" + args.hostname)

	# attr_types = get_most_common_attribute_types(driver, args.attr_number)
	attr_types = [('Organism', 1), ("Sex", 2)]

	for (attr, usage) in attr_types:
		print "{} - {:d}".format(attr, usage)
		mapping = get_ols_annotation(attr, "EFO")
		print "{!s}".format(mapping)



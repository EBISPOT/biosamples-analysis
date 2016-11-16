#pip install neo4j-driver wordcloud matplotlib pillow image
from neo4j.v1 import GraphDatabase, basic_auth

import csv
import matplotlib
import wordcloud
import random


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
	return "hsl(%d, 100%%, 100%%)" % random.randint(120, 160)


def get_most_common_attributes(db_driver, n_attributes):

	print 'Querying database for the %d most common attributes' % n_attributes
	attr_types = []
	with db_driver.session() as session:
		results = session.run("MATCH (s:Sample)-[:hasAttribute]->(:Attribute)-->(t:AttributeType) "
		                      "WITH t, COUNT(s) AS usage_count "
		                      "RETURN t.attributeTypeId as type, usage_count "
		                      "ORDER BY usage_count DESC "
		                      "LIMIT %d" % n_attributes)
		for record in results:
			attr_types.append(record['type'])
	return attr_types


def generate_spreadsheet(db_driver):

	print "generating spreadsheet of most common attribute types and values"
	with open("attr_common.csv", "w") as outfile:
		csvout = csv.writer(outfile)

		with db_driver.session() as session:
			results = session.run("MATCH (s:Sample)-[:hasAttribute]->(:Attribute)-->(t:AttributeType) WITH t, COUNT(s) AS usage_count RETURN t.attributeTypeId as type, usage_count ORDER BY usage_count DESC LIMIT 100")
			for result in results:
				print "{} ({})".format(result["type"], result["usage_count"])

				row = ["{} ({})".format(result["type"], result["usage_count"])]

				with db_driver.session() as session2:
					cypher = "MATCH (s:Sample)-->(a:Attribute)-->(t:AttributeType{attributeTypeId:'"+str(result["type"])+"'}), (a:Attribute)-->(v:AttributeValue) WITH t,v,COUNT(s) AS usage_count RETURN t.attributeTypeId AS type, v.attributeValueId AS value, usage_count ORDER BY usage_count DESC LIMIT 10"
					print cypher
					results2 = session2.run(cypher)
					for result2 in results2:
						row.append("{} ({})".format(result2["value"], result2["usage_count"]))
						print "{} | {} ({})".format(result2["type"], result2["value"], result2["usage_count"])

				csvout.writerow(row)

	print "generated spreadsheet of most common attribute types and values"


def generate_wordcloud(db_driver):

	print "generating wordcloud of most common attribute types and values"
	freq = []
	with db_driver.session() as session:
		results = session.run("MATCH (s:Sample)-[:hasAttribute]->(:Attribute)-->(t:AttributeType) WITH t, COUNT(s) AS usage_count RETURN t.attributeTypeId as type, usage_count ORDER BY usage_count DESC LIMIT 1000")
		i = 0
		for result in results:
			freq.append((result["type"], result["usage_count"]))
			if i < 25:
				i += 1
				print "generating wordcloud of values of", result["type"]
				freq2 = []
				with db_driver.session() as session2:
					cypher = \
						"MATCH (s:Sample)-->(a:Attribute)-->(t:AttributeType{attributeTypeId:'" + str(result["type"]) + "'}), (a:Attribute)-->(v:AttributeValue) " \
						"WITH t,v,COUNT(s) AS usage_count " \
						"RETURN t.attributeTypeId AS type, v.attributeValueId AS value, usage_count " \
						"ORDER BY usage_count DESC " \
						"LIMIT 1000"
					results2 = session2.run(cypher)
					for result2 in results2:
						freq2.append((result2["value"],result2["usage_count"]))
				wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=1000).generate_from_frequencies(freq2)
				wc.recolor(color_func=grey_color_func, random_state=3)
				wc.to_file("cloud-values-{}.png".format(result["type"]))
				print "generated wordcloud of values of", result["type"]
		wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=1000).generate_from_frequencies(freq).to_file("cloud-types.png")
	print "generated wordcloud of most common attribute types and values"


def attribute_values_mapped(db_driver):

	print "generating the list with the percentage of attributes values mapped to ontology term"
	common_attrs = get_most_common_attributes(db_driver, 10)
	limit_results = 10
	for attr in common_attrs:
		cypher = "MATCH (s:Sample)-->(a:Attribute{type: \"%s\"})-->(ot:OntologyTerm) " \
                 "RETURN s.accession AS Sample, " \
		         "COUNT(a) AS Attributes, " \
		         "COUNT(ot) AS AttributesMapped, " \
		         "COUNT(ot)/COUNT(a) AS Ratio " \
                 "ORDER BY Attributes DESC LIMIT %d" % (attr, limit_results)
		with db_driver.session() as session:
			results = session.run(cypher)
			for record in results:
				print record


if __name__ == "__main__":
	
	driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "password"))
	
	# spreadsheet of most common attribute types and values
	# generate_spreadsheet(driver)
	
	# wordcloud of most common attribute types and values
	# generate_wordcloud(driver)

	# Percentage of attribute values mapped to ontology for each attribute type
	attribute_values_mapped(driver)
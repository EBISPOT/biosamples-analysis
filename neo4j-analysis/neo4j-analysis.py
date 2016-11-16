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
		                      "RETURN t.name as type, usage_count "
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
			results = session.run("MATCH (s:Sample)-->(a:Attribute)-->(t:AttributeType) WITH a.type AS type, COUNT(s) AS usage_count RETURN type, usage_count ORDER BY usage_count DESC LIMIT 100")
			for result in results:
				print "{} ({})".format(result["type"], result["usage_count"])

				row = ["{} ({})".format(result["type"], result["usage_count"])]

				with db_driver.session() as session2:
					cypher = "MATCH (s:Sample)-->(a:Attribute{type:'" + str(result["type"]) + "'})-->(v:AttributeValue) WITH v,COUNT(s) AS usage_count RETURN v.attributeValueId AS value, usage_count ORDER BY usage_count DESC LIMIT 10"
					print cypher
					results2 = session2.run(cypher)
					for result2 in results2:
						row.append("{} ({})".format(result2["value"], result2["usage_count"]))
						print "{} ({})".format(result2["value"], result2["usage_count"])

				csvout.writerow(row)

	print "generated spreadsheet of most common attribute types and values"


def generate_wordcloud(db_driver):

	print "generating wordcloud of most common attribute types and values"
	freq = []
	with db_driver.session() as session:
		results = session.run("MATCH (s:Sample)-->(a:Attribute) WITH a,COUNT(s) AS usage_count RETURN a.type, usage_count ORDER BY usage_count DESC LIMIT 1000")
		i = 0
		for result in results:
			freq.append((result["a.type"], result["usage_count"]))
			if i < 25:
				i += 1
				print "generating wordcloud of values of", result["a.type"]
				freq2 = []
				with db_driver.session() as session2:
					cypher = \
						"MATCH (s:Sample)-->(a:Attribute{type:'" + str(result["a.type"]) + "'}) " \
						"WITH a,COUNT(s) AS usage_count " \
						"RETURN a.value AS value, usage_count " \
						"ORDER BY usage_count DESC " \
						"LIMIT 1000"
					results2 = session2.run(cypher)
					for result2 in results2:
						freq2.append((result2["value"], result2["usage_count"]))
				wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=1000).generate_from_frequencies(freq2)
				wc.recolor(color_func=grey_color_func, random_state=3)
				wc.to_file("word_clouds/cloud-values-{}.png".format(result["a.type"]))
				print "generated wordcloud of values of", result["a.type"]
		wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=1000).generate_from_frequencies(freq).to_file("word_clouds/cloud-types.png")
	print "generated wordcloud of most common attribute types and values"


def attribute_values_mapped(db_driver):

	print "generating the list with the percentage of attributes values mapped to ontology term"
	with open("perc_attr_mapped.csv", "w") as outfile:
		csvout = csv.writer(outfile)

		common_attrs = get_most_common_attributes(db_driver, 100)
		for attr in common_attrs:
			cypher = "MATCH (s:Sample)-->(a:Attribute{type: \"%s\"}) " \
					 "RETURN COUNT(s) AS samples, " \
					 "COUNT(a.iri) AS mapped " % attr
			with db_driver.session() as session:
				result = session.run(cypher)
				for record in result:
					row = [str(attr), round(float(record["mapped"])*100/record["samples"], 2)]
					print row
					csvout.writerow(row)
				# print "%s: Ratio=%.2f" % (attr, float(record["mapped"])/record["samples"])


if __name__ == "__main__":
	
	driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "password"))
	
	# spreadsheet of most common attribute types and values
	#generate_spreadsheet(driver)
	
	# wordcloud of most common attribute types and values
	generate_wordcloud(driver)

	# Percentage of attribute values mapped to ontology for each attribute type
	attribute_values_mapped(driver)

# pip install neo4j-driver wordcloud matplotlib pillow image
from neo4j.v1 import GraphDatabase, basic_auth

import argparse
import csv
import wordcloud
import random
import numpy as np


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
	return "hsl(%d, 100%%, 100%%)" % random.randint(120, 160)


def get_most_common_attributes(db_driver, n_attributes):
	print 'Querying database for the %d most common attributes' % n_attributes
	attr_types = []
	with db_driver.session() as session:
		results = session.run("MATCH (s:Sample)-[:hasAttribute]->(:Attribute)-->(t:AttributeType) "
		                      "WITH t, COUNT(s) AS usage_count "
		                      "RETURN t.name AS type, usage_count "
		                      "ORDER BY usage_count DESC "
		                      "LIMIT %d" % n_attributes)
		for result in results:
			attr_types.append((result["type"], result["usage_count"]))
	return attr_types


def generate_spreadsheet(db_driver):
	print "generating spreadsheet of most common attribute types and values"
	with open("attr_common.csv", "w") as outfile:
		csvout = csv.writer(outfile)

		common = get_most_common_attributes(db_driver, 100)
		for attr in common:
			print "{} ({})".format(attr[0], attr[1])

			row = ["{} ({})".format(attr[0], attr[1])]

			with db_driver.session() as session2:
				cypher = "MATCH (s:Sample)-->(a:Attribute)-->(t:AttributeType{name:'"+attr[0]+"'}), (a:Attribute)-->(v:AttributeValue) RETURN v.name AS value, COUNT(s) AS usage_count ORDER BY usage_count DESC LIMIT 10"
				#print cypher
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

	common = get_most_common_attributes(db_driver, 1000)
	for attr in common:
		i = 0
		freq.append((attr[0], attr[1]))
		if i < 10:
			i += 1
			print "generating wordcloud of values of", attr[0]
			freq2 = []
			with db_driver.session() as session2:
				cypher = \
					"MATCH (s:Sample)-->(a:Attribute)-->(t:AttributeType{name:'"+attr[0]+"'}), (a:Attribute)-->(v:AttributeValue) RETURN v.name AS value, COUNT(s) AS usage_count ORDER BY usage_count DESC LIMIT 1000"
				results2 = session2.run(cypher)
				for result2 in results2:
					freq2.append((result2["value"], result2["usage_count"]))
			wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=1000).generate_from_frequencies(freq2)
			wc.recolor(color_func=grey_color_func, random_state=3)
			wc.to_file("word_clouds/cloud-values-{}.png".format(attr[0]))
			print "generated wordcloud of values of", attr[0]
		wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=1000).generate_from_frequencies(freq)
		wc.recolor(color_func=grey_color_func, random_state=3)
		wc.to_file("word_clouds/cloud-types.png")
	print "generated wordcloud of most common attribute types and values"


def attribute_values_mapped(db_driver):
	print "generating the list with the percentage of attributes values mapped to ontology term"
	with open("perc_attr_mapped.csv", "w") as outfile:
		csvout = csv.writer(outfile)

		common_attrs = get_most_common_attributes(db_driver, 200)
		for attr in common_attrs:
			cypher = "MATCH (s:Sample)-->(a:Attribute{type:'" + attr[0] + "'}) " \
			                                                              "RETURN COUNT(s) AS samples, " \
			                                                              "COUNT(a.iri) AS mapped "
			with db_driver.session() as session:
				result = session.run(cypher)
				for record in result:
					print attr, record["samples"], record["mapped"]
					row = [str(attr[0]), attr[1], round(float(record["mapped"]) * 100 / record["samples"], 2)]
					print row
					csvout.writerow(row)
				# print "%s: Ratio=%.2f" % (attr, float(record["mapped"])/record["samples"])


def attribute_value_coverage(db_driver):
	
	print "generating coverage stats"
	prop = 0.75
	maxcount = 100
	
	common_attrs = get_most_common_attributes(db_driver, 100)
	for attr in common_attrs:
		cypher = "MATCH (s:Sample)--(a:Attribute)--(t:AttributeType{name:'"+attr[0]+"'}), (a)--(v:AttributeValue) RETURN v.name, count(s) AS count_s ORDER BY count(s) DESC"
		#print cypher
		with db_driver.session() as session:
			result = session.run(cypher)
			running_total = 0
			i = 0
			for record in result:
				i += 1
				running_total += record["count_s"]
				#print attr[1], float(attr[1])*prop, running_total, record["count_s"]
				if running_total > float(attr[1])*prop:
					print "for type",attr[0],"the top",i,"values cover",int(prop*100.0),"% of samples"
					break
				if i >= maxcount:
					print "for type",attr[0],"the top",maxcount,"values do not cover",int(prop*100.0),"% of samples"

	
def number_of_attributes_ditribution(db_driver, show_graph):
	print "generating the spreadsheet with Number of attributes frequencies among samples"
	with open("num_attributes_distribution.csv", "w") as outfile:
		csvout = csv.writer(outfile)
		csvout.writerow(["attr_count", "samples_count"])
		print "Attr_count, Samples_count"
		cypher = "MATCH (s:Sample)-[:hasAttribute]->(:Attribute)-[:hasType]->(at:AttributeType) \
					  WITH s, COUNT(DISTINCT at) AS attr_count \
					  RETURN attr_count, COUNT(s) as samples_count \
					  ORDER BY attr_count DESC LIMIT 100"
		n_attr = []
		n_samples = []
		with db_driver.session() as session:
			results = session.run(cypher)
			for record in results:
				n_attr.append(record["attr_count"])
				n_samples.append(record["samples_count"])
				print "%s, %d" % (record["attr_count"], record["samples_count"])
				csvout.writerow([record["attr_count"], record["samples_count"]])
		if show_graph:
			plt.bar(n_attr, n_samples)
			plt.gca().set_yscale("log")
			plt.gca().set_xlabel("Number of attributes per sample")
			plt.gca().set_ylabel("Number of samples")
			plt.show()


def number_of_values_per_type(db_driver, show_graph):
	print "generating spreadsheet with number of values for each attribute type"
	with open("num_values_distribution.csv", "w") as fileout:
		csvout = csv.writer(fileout)

		cypher = "MATCH (s:Sample)-->(a:Attribute)-->(at:AttributeType) \
                  WITH at.name AS attr_type, COUNT(DISTINCT a.value) AS n_values, COUNT(s) AS n_samples \
                  RETURN attr_type, n_values, n_samples, toFloat(n_values)/toFloat(n_samples) AS ratio \
                  ORDER BY ratio \
                  LIMIT 100"
		print "%s, %s, %s, %s" % ("Attribute type", "Number of values", "Number of samples", "Ratio")
		csvout.writerow(["Attribute type", "Number of values", "Number of samples", "Ratio"])
		values = []
		with db_driver.session() as session:
			results = session.run(cypher)
			for record in results:
				record_tuple = (record["attr_type"],
				                record["n_values"],
				                record["n_samples"],
				                record["ratio"])
				print "%s, %d, %d, %.2f" % record_tuple
				values.append(record_tuple)
				csvout.writerow([x for x in record_tuple])
		attr_types, n_values, n_samples, ratios = map(list, zip(*values))
		counts = np.bincount(n_values)
		stats = {"mean": np.mean(n_values), "median": np.median(n_values), "mode": np.argmax(counts)}

		print "Mean: %d" % (stats["mean"])
		print "Median: %d" % (stats["median"])
		print "Mode: %d" % (stats["mode"])

		if show_graph:
			fig = plt.figure()
			ax1 = fig.add_subplot(211)
			ax1.bar(np.arange(len(n_values)), n_values)
			ax1.set_yscale("log")
			ax1.set_xticks(np.arange(len(n_values)))
			ax1.set_ylabel("Number of attribute values")

			ax2 = fig.add_subplot(212)
			ax2.bar(np.arange(len(n_values)), ratios)
			ax2.set_xticks(np.arange(len(n_values)))
			ax2.set_xticklabels(attr_types, rotation="vertical")
			ax2.set_xlabel("Attribute types")
			ax2.set_ylabel("Values diversity within samples")
			plt.show()


def main_func(db_driver, graph):

	# spreadsheet of most common attribute types and values
	# generate_spreadsheet(driver)

	# wordcloud of most common attribute types and values
	# generate_wordcloud(driver)

	# Percentage of attribute values mapped to ontology for each attribute type
	# attribute_values_mapped(driver)

	# Number of attributes per sample
	# number_of_attributes_ditribution(driver, show_graph)

	# Number of attribute values per attribute type
	number_of_values_per_type(db_driver, graph)

	# top N values to cover P proportion of samples
	attribute_value_coverage(driver)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--graph', '-g', type=bool, default=False)
	args = parser.parse_args()

	driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "password"))
	if args.graph:
		import matplotlib.pyplot as plt

	main_func(driver, args.graph)

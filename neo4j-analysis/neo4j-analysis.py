# pip install neo4j-driver wordcloud matplotlib pillow image unicodecsv
from __future__ import unicode_literals
import argparse
import csv
import matplotlib
import numpy as np
import os
import random
import wordcloud
import unicodecsv
import re
import timeit
import requests
from neo4j.v1 import GraphDatabase, basic_auth

matplotlib.use('Agg')
import matplotlib.pyplot


def get_attribute_type_iri(attr_type):
	mapping = {
		"Sex": "http://purl.obolibrary.org/obo/PATO_0000047",
		"Organism Part": "http://www.ebi.ac.uk/efo/EFO_0000635",
		"Organism": "http://purl.obolibrary.org/obo/OBI_0100026",
		"Cell Type": "http://www.ebi.ac.uk/efo/EFO_0000324",
		"Developmental Stage": "http://www.ebi.ac.uk/efo/EFO_0000399",
		"Cultivar": "http://www.ebi.ac.uk/efo/EFO_0005136",
		"Ethnicity": "http://www.ebi.ac.uk/efo/EFO_0001799",
		"Race": "http://www.ebi.ac.uk/efo/EFO_0001799",
		"Disease State": "http://www.ebi.ac.uk/efo/EFO_0000408"
	}

	if not attr_type in mapping:
		return None
	else:
		return mapping[attr_type]


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
	return "hsl(%d, 100%%, 100%%)" % random.randint(120, 160)


def get_most_common_attributes(db_driver, n_attributes, force=True):
	attr_types = []
	if n_attributes == 0:
		return attr_types
	else:
		if not force and os.path.isfile('neo4j-analysis/csv/attr_common.csv'):
			with open('neo4j-analysis/csv/attr_common.csv', 'r') as f:
				attr_re = re.compile("(?P<type>(?:\w+\s?)+)\s\((?P<usage_count>\d+)\)")
				csv_reader = unicodecsv.reader(f)
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


def get_usage_count(db_driver, attr_type):
	with db_driver.session() as session:
		results = session.run("MATCH (s:Sample)-[u:hasAttribute]->(:Attribute{type:{attr_type}}) "
		                      "RETURN COUNT(u) AS usage_count", {"attr_type": attr_type})
		for result in results:
			return result["usage_count"]


def get_total_attribute_usage(db_driver):
	with db_driver.session() as session:
		results = session.run("MATCH (:Sample)-[u:hasAttribute]->(:Attribute) RETURN COUNT(u)")
	for result in results:
		return result[0]


def generate_summary(args, db_driver):
	print "generating summary of most common attribute types and values"

	generate_summary_spreadsheet(args, db_driver)

	generate_summary_plots(args, db_driver)

	generate_summary_wordcloud(args, db_driver)

	print "generated summary of most common attribute types and values"


def generate_summary_spreadsheet(args, db_driver):
	print "generating summary spreadsheet of most common attribute types and values"
	common = get_most_common_attributes(db_driver, 250, force=True)

	try:
		os.makedirs(args.path)
	except OSError:
		pass

	with open(args.path + "/attr_common.csv", "w") as outfile:
		csvout = unicodecsv.writer(outfile)

		for attr in common:
			row = ["{} ({})".format(attr[0], attr[1])]

			with db_driver.session() as session2:
				cypher = "MATCH (s:Sample)-[u:hasAttribute]->(a:Attribute)-->(t:AttributeType{name: {attr_type}}), \
                            (a:Attribute)-->(v:AttributeValue) \
                            RETURN v.name AS value, COUNT(u) AS usage_count ORDER BY usage_count DESC LIMIT 25"
				results2 = session2.run(cypher, {"attr_type": attr[0]})
				for result2 in results2:
					row.append("{} ({})".format(result2["value"], result2["usage_count"]))

			csvout.writerow(row)

	print "generated summary spreadsheet of most common attribute types and values"


def generate_summary_plots(args, db_driver):
	print "generating summary plots of most common attribute types and values"

	cypher = "MATCH (s:Sample)-->(a:Attribute) \
                  WITH s, COUNT(DISTINCT a) AS attr_count \
                  RETURN attr_count, COUNT(s) as samples_count \
                  ORDER BY attr_count ASC"
	n_attr = []
	n_samples = []
	with db_driver.session() as session:
		results = session.run(cypher)
		for record in results:
			n_attr.append(record["attr_count"])
			n_samples.append(record["samples_count"])
	fig = matplotlib.pyplot.figure(figsize=(12, 6))
	axis = fig.add_axes((0.0, 0.0, 1.0, 1.0), title="Frequency distribution of number of attributes on each sample")
	axis.bar(n_attr, n_samples)
	axis.set_yscale("log")
	axis.set_xlabel("Number of attributes")
	axis.set_ylabel("Frequency")

	try:
		os.makedirs(args.path)
	except OSError:
		pass
	fig.savefig(args.path + "/freq-of-number-attrs.png", bbox_inches='tight')

	"""
    There are some samples that have many many attributes. Typically, these are survey results
    e.g. SAMEA4394014
    """
	print "generated summary plots of most common attribute types and values"


def generate_summary_wordcloud(args, db_driver):
	max_words = args.wordcloud_entries
	if max_words < 1:
		return

	freq = []

	print "generating wordcloud of most common attribute types and values"
	common = get_most_common_attributes(db_driver, max_words)
	for attr in common:
		freq.append((attr[0], attr[1]))

	wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=max_words).generate_from_frequencies(freq)
	wc.recolor(color_func=grey_color_func, random_state=3)
	try:
		os.makedirs(args.path + "/word_clouds")
	except OSError:
		pass
	wc.to_file(args.path + "/word_clouds/cloud-types.png")
	print "generated wordcloud of most common attribute types and values"


def generate_wordcloud_of_attribute(args, db_driver, attr_type, usage_count):
	max_words = args.wordcloud_entries
	if max_words < 1:
		return

	freq2 = []

	print "generating wordcloud of values of", attr_type
	with db_driver.session() as session2:
		cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute)-->(t:AttributeType{name:{attr_type}}), (a:Attribute)-->(v:AttributeValue) " \
		         "RETURN v.name AS value, COUNT(u) AS usage_count ORDER BY usage_count DESC LIMIT {max_words}"
		cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}}) \
            RETURN a.value AS value, count(u) AS usage_count \
            ORDER BY count(u) DESC \
            LIMIT {max_words}"
		results2 = session2.run(cypher, {"attr_type": attr_type, "max_words": max_words})
		for result2 in results2:
			freq2.append((result2["value"], result2["usage_count"]))
	if len(freq2) > 0:
		wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=max_words).generate_from_frequencies(freq2)
		wc.recolor(color_func=grey_color_func, random_state=3)
		try:
			os.makedirs(args.path + "/word_clouds")
		except OSError:
			pass
		wc.to_file(args.path + "/word_clouds/cloud-values-{:07d}-{}.png".format(usage_count, attr_type))
		print "generated wordcloud of values of", attr_type


def attribute_value_mapped(args, db_driver, attr_type, usage_count):
	"""
    Return the number of values for an attribute type that are mapped to an ontology term
    """
	cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}}) " \
	         "RETURN COUNT(u) AS usage_count, COUNT(a.iri) AS mapped "
	with db_driver.session() as session:
		result = session.run(cypher, {"attr_type": attr_type})
		for record in result:
			if float(usage_count) > 0:
				prop = float(record["mapped"]) / float(usage_count)
				print "for type '{:s}' ontologies terms are mapped for {:.0%} of uses".format(attr_type, prop)
				return prop
			else:
				print "for type '{:s}' ontologies terms are mapped for 0% of uses".format(attr_type)
				return 0


def attribute_value_mapped_label_match(args, db_driver, attr_type, usage_count):
	"""
    Return the number of values for an attribute type that are coincident with the label of the ontology term they're
    mapped to or one of its synonyms
    """
	cypher = 'MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}})-->(:OntologyTerm)-->(ols:OLS) \
        WHERE ols.label = a.value OR a.value IN ols.`synonyms[]`\
        RETURN COUNT(DISTINCT u) AS label_match_count'
	with db_driver.session() as session:
		result = session.run(cypher, {"attr_type": attr_type})
		for record in result:
			if float(usage_count) > 0:
				prop = float(record["label_match_count"]) / float(usage_count)
				print "for type '{:s}' ontologies terms match label or synonym for {:.0%} of uses".format(attr_type,
				                                                                                          prop)
				return prop
			else:
				print "for type '{:s}' ontologies terms match label or synonym for 0% of uses".format(attr_type)
				return 0


def attribute_value_coverage(args, db_driver, attr_type, usage_count, prop, maxcount):
	"""
    Return the number of attribute values that cover a proportion of attribute within a max count
    """
	with db_driver.session() as session:
		cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}}) \
            RETURN a.value, count(u) AS count_s \
            ORDER BY count(u) DESC \
            LIMIT {maxcount}"
		result = session.run(cypher, {"attr_type": attr_type, "maxcount": maxcount})
		running_total = 0
		i = 0
		for record in result:
			i += 1
			running_total += record["count_s"]
			if running_total > float(usage_count) * prop:
				print "for type '{:s}' the top {:d} values cover {:.0%} of uses".format(attr_type, i, prop)
				return i
			if i >= maxcount:
				print "for type '{:s}' the top {:d} values do not cover {:.0%} of uses".format(attr_type, maxcount,
				                                                                               prop)
				return None


def number_of_values_per_type(args, db_driver):
	"""
    Generate a spreadsheet with the number of values for each attribute type
    """
	print "generating spreadsheet with number of values for each attribute type"
	try:
		os.makedirs(args.path)
	except OSError:
		pass
	with open(args.path + "/num_values_distribution.csv", "w") as fileout:
		csvout = unicodecsv.writer(fileout)

		cypher = "MATCH (s:Sample)-->(a:Attribute)-->(at:AttributeType) \
                  WITH at.name AS attr_type, COUNT(DISTINCT a.value) AS n_values, COUNT(s) AS n_samples \
                  RETURN attr_type, n_values, n_samples, toFloat(n_values)/toFloat(n_samples) AS ratio \
                  ORDER BY n_samples DESC \
                  LIMIT 50"
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
				# print "%s, %d, %d, %.2f" % record_tuple
				values.append(record_tuple)
				csvout.writerow([x for x in record_tuple])
		attr_types, n_values, n_samples, ratios = map(list, zip(*values))
		counts = np.bincount(n_values)
		stats = {"mean": np.mean(n_values), "median": np.median(n_values), "mode": np.argmax(counts)}

		print "Mean: %d" % (stats["mean"])
		print "Median: %d" % (stats["median"])
		print "Mode: %d" % (stats["mode"])

		fig = matplotlib.pyplot.figure(figsize=(24, 18))

		ax1 = fig.add_subplot(211)
		ax1.bar(np.arange(len(n_values)), n_values, align="center")
		ax1.set_yscale("log")
		ax1.set_xticks(np.arange(len(n_values)))
		ax1.set_ylabel("Number of attribute values")

		ax2 = fig.add_subplot(212)
		ax2.bar(np.arange(len(n_values)), ratios, align="center")
		ax2.set_xticks(np.arange(len(n_values)))
		ax2.set_xticklabels(attr_types, rotation=90)
		ax2.set_xlabel("Attribute types")
		ax2.set_ylabel("Diversity of values")

		try:
			os.makedirs(args.path)
		except OSError:
			pass
		fig.savefig(args.path + "/value-diversity.png", bbox_inches='tight')


def attribute_value_child(args, db_driver, attr_type, usage_count, iri):
	values = dict()
	with db_driver.session() as session:
		cypher = \
			"MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}}) " \
			"OPTIONAL MATCH (a)-[:hasIri]->(:OntologyTerm)-->(:OLS)" \
			"-[:hasParent*1..]->(eo:OLS{iri:{iri}}) " \
			"RETURN count(distinct u) as count, eo IS NULL as ontology_missing"
		results = session.run(cypher, {"attr_type": attr_type, "iri": iri})
		for record in results:
			if record["ontology_missing"]:
				values["missing"] = record["count"]
			else:
				values["not_missing"] = record["count"]

	count = values["not_missing"] if "not_missing" in values else 0
	if float(usage_count) > 0:
		prop = float(count) / float(usage_count)
		print "for type '{:s}' ontologies terms are a child term for {:.0%} of uses".format(attr_type, prop)


def attribute_value_mapped_obsolete(args, db_driver, attr_type, usage_count):
	"""
    Return the percentage of attribute that are mapped to an obsolete ontology term
    """
	total = 0
	with db_driver.session() as session:
		cypher = \
			"MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}})" \
			"-->(o:OntologyTerm)-->(efo:OLS{obsolete:'True'}) " \
			"RETURN DISTINCT a.value AS value, COUNT(u) AS count, o.iri AS iri"
		results = session.run(cypher, {"attr_type": attr_type})
		for record in results:
			total += record["count"]

	if float(usage_count) > 0:
		prop = float(total) / float(usage_count)
		print "for type '{:s}' ontologies terms are obsolete for {:.0%} of uses".format(attr_type, prop)


def check_attribute_type_casing(args, db_driver, attr_type):
	"""
    Check the available cases available in the database for the attribute type
    """

	cypher = 'MATCH (a:AttributeType) ' \
	         'WHERE LOWER(a.name)=LOWER({attr_type}) ' \
	         'RETURN COUNT(a.name) as number, collect(a.name) AS values'

	with db_driver.session() as session:
		results = session.run(cypher, {"attr_type": attr_type})

		for result in results:
			print "for type '{:s}' the possible cases are {:d}: {:s}".format(
				attr_type,
				result["number"],
				", ".join(result["values"])
			)


def check_common_values(args, db_driver, attr_type_a, attr_type_b):
	"""
    Check the number of values that are shared between to attribute types
    """
	global similar_terms_b, values_b
	attr_values_query = "MATCH (a:Attribute{type:{type}}) RETURN a.value"
	similar_values_query = "CALL apoc.index.search('attributes','Attribute.value:\"{value}\"') " \
	                       "YIELD node MATCH (node) WHERE node.type='{type}' " \
	                       "RETURN DISTINCT node.value AS value"
	similar_terms = []
	similar_terms_tuples = []
	values_b = []
	with db_driver.session() as session:
		results = list(session.run(attr_values_query, {"type": attr_type_a}))
		values_a = results

		results = list(session.run(attr_values_query, {"type": attr_type_b}))
		values_b = results

		for value in values_b:
			sanitized_value = value[0].replace("'", r"\'")
			results = list(session.run(similar_values_query.format(type=attr_type_a, value=sanitized_value)))
			new_similar_terms = [item["value"] for item in results if item["value"] not in similar_terms]
			if len(new_similar_terms) > 0:
				similar_terms.append(value)
			similar_terms_tuples.extend([(value[0], item) for item in new_similar_terms])

	perc_similar_values_b = 100 * float(len(similar_terms)) / len(values_b)
	print "{type_a:s} covers {perc:.2f}% of terms in {type_b:s}".format(
		type_a=attr_type_a, type_b=attr_type_b, perc=perc_similar_values_b
	)


# common_values = filter(set(values_attr_type_a).__contains__, values_attr_type_b)
# values_a_count = len(values_attr_type_a)
# values_b_count = len(values_attr_type_b)
# common_values_count = len(common_values)
# unique_values_a = [item for item in values_attr_type_a if item not in common_values]
# unique_values_b = [item for item in values_attr_type_b if item not in common_values]
#
# unique_a_perc = 100 * (float(values_a_count - common_values_count) / values_a_count)
# shared_a_perc = 100 - unique_a_perc
# unique_b_perc = 100 * (float(values_b_count - common_values_count) / values_b_count)
# shared_b_perc = 100 - unique_b_perc

# print "comparing {attr_a:s} and {attr_b:s}: " \
#       "\n\tfor {attr_a:s} {shared_a:.2f}% of values are shared and {unique_a:.2f} are unique, " \
#       "\n\tfor {attr_b:s} {shared_b:.2f}% of values are shared and {unique_b:.2f} are unique".format(
#   attr_a=attr_type_a, attr_b=attr_type_b,
#   shared_a=shared_a_perc, shared_b=shared_b_perc,
#   unique_a=unique_a_perc, unique_b=unique_b_perc)


# print "some unique values for '{attr_a:s}' are: \n\t {unique_a:s}\n" \
#       "some unique values for '{attr_b:s}' are: \n\t {unique_b:s}\n" \
#       "some of the common values between '{attr_a:s}' and '{attr_b:s}' are: \n\t{common_values:s}".format(
#   attr_a=attr_type_a, attr_b=attr_type_b,
#   unique_a=', '.join(unique_values_a[:5]), unique_b=', '.join(unique_values_b[:5]),
#   common_values=', '.join(common_values[:5]))


def find_clusters(driver, target):
	print "trying to do some clustering stuff"
	# 1) for each sample, walk up the ncbi taxonomy tree and add one to each node
	# 2) make a set of leaf nodes
	# 3) find the leaf-but-one node with the loweset score
	# 4) remove the leaf nodes of the leaf-but one from the set
	# 5) add the leaf-but-one as a new leaf
	# 6) repeat from 3) until there is a sufficiently low number (10)

	raw_scores = {}
	scores = {}
	parents = {}
	children = {}
	labels = {}
	leaves = list()
	with driver.session() as session:

		# print "getting parents"
		results = session.run("""MATCH (m:ncbitaxonOntologyTerm)-[:hasParent]->(n:ncbitaxonOntologyTerm)
                RETURN DISTINCT m.iri AS m, m.label as mlabel, n.iri AS n""")
		for result in results:
			parents[result["m"]] = result["n"]
			labels[result["m"]] = result["mlabel"]
			if result["n"] not in children:
				children[result["n"]] = set()
			children[result["n"]].add(result["m"])
		# print "got",len(parents), "parents"
		# print "got",len(children), "children"

		# print "getting raw_scores"
		results = session.run(
			"""MATCH (s:Sample)-[:hasAttribute]->(:Attribute{type:'Organism'})-[:hasIri]->()-[:inNcbitaxon]->(n:ncbitaxonOntologyTerm) RETURN count(distinct s) AS s, n.iri AS n""")
		for result in results:
			raw_scores[result["n"]] = int(result["s"])
		# print "got",len(raw_scores), "raw_scores"

		# print the top 10 raw scores

		topscores = sorted(raw_scores.viewkeys(), reverse=True, key=lambda iri: raw_scores[iri])
		for topscore in topscores[:10]:
			print "found raw score", "'" + labels[topscore] + "'", "(", topscore, ")", "with score", raw_scores[
				topscore]

		def getscore(iri):
			if iri in scores:
				return scores[iri]
			score = 0
			if iri in children:
				score = score + sum((getscore(i) for i in children[iri]))
			if iri in raw_scores:
				score = score + raw_scores[iri]
			scores[iri] = score
			return scores[iri]

		# print "calculating scores"
		for iri in parents:
			getscore(iri)
		# print "calculated scores"

		# calculate watershed
		totalscore = sum(raw_scores.viewvalues())
		maxscore = max(scores.viewvalues())
		# print "totalscore","=",totalscore
		# print "maxscore","=",maxscore

		watershed = maxscore / target
		# print "watershed","=",watershed

		bignodes = set([n for n in scores if scores[n] >= watershed])
		print len(bignodes), "nodes over watershed"

		# now find leaf nodes in the subset above the watershed
		bigleaves = set()
		for bignode in bignodes:
			if bignode not in children:
				bigleaves.add(bignode)
			elif len(children[bignode] & bignodes) == 0:
				bigleaves.add(bignode)

		for bigleaf in sorted(bigleaves, key=lambda bigleaf: scores[bigleaf]):
			print "found big leaf", "'" + labels[bigleaf] + "'", "(", bigleaf, ")", "with score", scores[bigleaf]
			# print "found", len(bigleaves),"big leaves"


def get_attributes_by_category():
	"""
    Read the categories file and return a dictionary containing all the attributes separated by categories
    """
	categories = dict()
	with open('neo4j-analysis/csv/attribute_categories.csv', 'r') as f:
		csv_reader = unicodecsv.reader(f)
		for row in csv_reader:
			if len(row) == 2:
				attr_type = row[0]
				cat = row[1]
				if cat not in categories.keys():
					categories[cat] = []
				categories[cat].append(attr_type)

	return categories


def get_gold_grade_attributes(db_driver, attr_type):
	pass


def get_silver_grade_attributes(db_driver, attr_type):
	pass


def get_gold_grade_samples(db_driver):
	pass


def get_silver_grade_samples(db_driver):
	pass


def generate_categories_stats(db_driver):
	"""
    Return some stats based on different attribute categories
    """
	print "generating statistics for attribute categories"
	categories = get_attributes_by_category()
	total_samples = get_total_attribute_usage(db_driver=driver)
	categories_usage = {}
	for cat, attributes in categories.items():
		total_count = 0
		for attr in attributes:
			total_count += get_usage_count(db_driver=driver, attr_type=attr)
		categories_usage[cat] = 100 * float(total_count) / total_samples
		print "{cat:s} category covers {perc:.2f}% of the attribute usages".format(
			cat=cat, perc=categories_usage[cat]
		)


if __name__ == "__main__":
	print "Welcome to the BioSamples analysis"

	parser = argparse.ArgumentParser()
	parser.add_argument('--hostname', default="neo4j-server-local")
	parser.add_argument('--summary', action='store_true')
	parser.add_argument('--wordcloud-entries', type=int, default=1000)
	parser.add_argument('--top-attr', type=int, default=0)
	parser.add_argument('--cluster', type=int, default=0)

	# this will accept underscores and replace them with spaces in attribute types
	parser.add_argument('--attr', action='append')
	parser.add_argument('--path', default="out")

	args = parser.parse_args()

	driver = GraphDatabase.driver("bolt://" + args.hostname)

	print "Generation of reports started"
	generate_categories_stats(db_driver=driver)

	# spreadsheet of most common attribute types and values
	if args.summary:
		generate_summary(args, driver)

	attrs = get_most_common_attributes(driver, args.top_attr, force=False)
	if args.attr is not None:
		for attr in args.attr:
			attr = attr.replace("_", " ")
			usage_count = get_usage_count(driver, attr)
			attrs.append((attr, usage_count))

	for attr_type, usage_count in attrs:
		check_attribute_type_casing(args, driver, attr_type)
		generate_wordcloud_of_attribute(args, driver, attr_type, usage_count)
		attribute_value_mapped(args, driver, attr_type, usage_count)
		attribute_value_mapped_label_match(args, driver, attr_type, usage_count)
		attribute_value_mapped_obsolete(args, driver, attr_type, usage_count)
		attribute_value_coverage(args, driver, attr_type, usage_count, 0.50, 100)
		attribute_value_coverage(args, driver, attr_type, usage_count, 0.75, 250)
		attribute_value_coverage(args, driver, attr_type, usage_count, 0.95, 500)
		iri = get_attribute_type_iri(attr_type)

		if iri is not None:
			attribute_value_child(args, driver, attr_type, usage_count, iri)

		if attr_type == "Disease State":
			check_common_values(args, driver, "Disease State", "Host Disease")
			check_common_values(args, driver, "Disease State", "Clinically Affected Status")
			check_common_values(args, driver, "Disease State", "Condition")
			check_common_values(args, driver, "Disease State", "Diagnosis")
			check_common_values(args, driver, "Disease State", "Infection")
			check_common_values(args, driver, "Disease State", "Disease Status")
			check_common_values(args, driver, "Disease State", "Clinical Information")
			check_common_values(args, driver, "Disease State", "Subset Diabetes")
			check_common_values(args, driver, "Disease State", "Subset Ibd")
			check_common_values(args, driver, "Disease State", "Health State")
			check_common_values(args, driver, "Disease State", "Disease")
			check_common_values(args, driver, "Disease State", "Host Health State")
			check_common_values(args, driver, "Disease State", "Status")
			check_common_values(args, driver, "Disease State", "Affected By")
			check_common_values(args, driver, "Disease State", "Clinical History")
			check_common_values(args, driver, "Disease State", "Tumor")
			check_common_values(args, driver, "Disease State", "Cause Of Death")

		if attr_type == "Organism":
			check_common_values(args, driver, "Organism", "Host")
			check_common_values(args, driver, "Organism", "Species")
			check_common_values(args, driver, "Organism", "Cell Type")
			check_common_values(args, driver, "Organism", "Host Tax Id")
			check_common_values(args, driver, "Organism", "Host Common Name")
			check_common_values(args, driver, "Organism", "Taxon Id")
			check_common_values(args, driver, "Organism", "Host Scientific Name")
			check_common_values(args, driver, "Organism", "Host Taxonomy Id")
			check_common_values(args, driver, "Organism", "Host Tissue Sampled")
			check_common_values(args, driver, "Organism", "Sub Species")
			check_common_values(args, driver, "Organism", "Host Taxid")
			check_common_values(args, driver, "Organism", "Host Taxon Id")

	if args.cluster > 0:
		find_clusters(driver, args.cluster)

	number_of_values_per_type(args, driver)
	number_of_uses_per_type(args, driver)

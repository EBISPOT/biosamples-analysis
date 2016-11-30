# pip install neo4j-driver wordcloud matplotlib pillow image
from neo4j.v1 import GraphDatabase, basic_auth

import argparse
import csv
import wordcloud
import random
import os
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "hsl(%d, 100%%, 100%%)" % random.randint(120, 160)


def get_most_common_attributes(db_driver, n_attributes):
    attr_types = []
    if n_attributes == 0:
        return attr_types
        
    print 'Querying database for the %d most common attribute types' % n_attributes
    with db_driver.session() as session:
        results = session.run("MATCH (:Sample)-[u:hasAttribute]->(a:Attribute) "
                              "RETURN a.type AS type, COUNT(u) AS usage_count "
                              "ORDER BY usage_count DESC "
                              "LIMIT {n_attributes}", {"n_attributes":n_attributes})
        for result in results:
            attr_types.append((result["type"], result["usage_count"]))
    return attr_types
    
def get_usage_count(db_driver, attr_type):
    with db_driver.session() as session:
        results = session.run("MATCH (s:Sample)-[u:hasAttribute]->(:Attribute{type:{attr_type}}) "
                              "RETURN COUNT(u) AS usage_count", {"attr_type":attr_type})
        for result in results:
            return result["usage_count"]
            
def generate_summary(args, db_driver):
    print "generating summary of most common attribute types and values"

    generate_summary_spreadsheet(args, db_driver)

    generate_summary_plots(args, db_driver)

    generate_summary_wordcloud(args, db_driver)

    print "generated summary of most common attribute types and values"


def generate_summary_spreadsheet(args, db_driver):
    print "generating summary spreadsheet of most common attribute types and values"
    common = get_most_common_attributes(db_driver, 100)

    try:
        os.makedirs("neo4j-analysis/csv")
    except OSError:
        pass

    with open("neo4j-analysis/csv/attr_common.csv", "w") as outfile:
        csvout = csv.writer(outfile)

        for attr in common:
            row = ["{} ({})".format(attr[0], attr[1])]

            with db_driver.session() as session2:
                cypher = "MATCH (s:Sample)-[u:hasAttribute]->(a:Attribute)-->(t:AttributeType{name: {attr_type}}), \
                            (a:Attribute)-->(v:AttributeValue) \
                            RETURN v.name AS value, COUNT(u) AS usage_count ORDER BY usage_count DESC LIMIT 10"
                results2 = session2.run(cypher, {"attr_type":attr[0]})
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
    fig = matplotlib.pyplot.figure(figsize=(12,6))
    axis = fig.add_axes((0.0,0.0,1.0,1.0), title="Frequency distribution of number of attributes on each sample")
    axis.bar(n_attr, n_samples)
    axis.set_yscale("log")
    axis.set_xlabel("Number of attributes")
    axis.set_ylabel("Frequency")

    try:
        os.makedirs("neo4j-analysis/plot")
    except OSError:
        pass
    fig.savefig("neo4j-analysis/plot/freq-of-number-attrs.png",bbox_inches='tight')

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
        os.makedirs("neo4j-analysis/word_clouds")
    except OSError:
        pass
    wc.to_file("neo4j-analysis/word_clouds/cloud-types.png")
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
        results2 = session2.run(cypher, {"attr_type":attr_type, "max_words":max_words})
        for result2 in results2:
            freq2.append((result2["value"], result2["usage_count"]))
    wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=max_words).generate_from_frequencies(freq2)
    wc.recolor(color_func=grey_color_func, random_state=3)
    try:
        os.makedirs("neo4j-analysis/word_clouds")
    except OSError:
        pass
    wc.to_file("neo4j-analysis/word_clouds/cloud-values-{:07d}-{}.png".format(usage_count,attr_type))
    print "generated wordcloud of values of", attr_type


def attribute_value_mapped(args, db_driver, attr_type, usage_count):
    cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}}) " \
        "RETURN COUNT(u) AS usage_count, COUNT(a.iri) AS mapped "
    with db_driver.session() as session:
        result = session.run(cypher, {"attr_type":attr_type})
        for record in result:
            prop = float(record["mapped"]) / float(usage_count)
            print "for type '{:s}' ontologies terms are mapped for {:.0%} of uses".format(attr_type,prop)
            return prop


def attribute_value_mapped_label_match(args, db_driver, attr_type, usage_count):
    cypher = 'MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}})-->(:OntologyTerm)-->(eo:EfoOntologyTerm) \
        WHERE eo.label = a.value OR a.value IN eo.`synonyms[]`\
        RETURN COUNT(u) AS label_match_count'
    with db_driver.session() as session:
        result = session.run(cypher, {"attr_type":attr_type})
        for record in result:
            prop = float(record["label_match_count"]) / float(usage_count)
            print "for type '{:s}' ontologies terms have the same value for {:.0%} of uses".format(attr_type,prop)
            return prop



def attribute_value_coverage(args, db_driver, attr_type, usage_count, prop, maxcount):
    
    with db_driver.session() as session:
        cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute)--(t:AttributeType{name:{attr_type}}), (a)--(v:AttributeValue) " \
            "RETURN v.name, count(u) AS count_s ORDER BY count(u) DESC"
        result = session.run(cypher, {"attr_type":attr_type})
        running_total = 0
        i = 0
        for record in result:
            i += 1
            running_total += record["count_s"]
            if running_total > float(usage_count)*prop:
                print "for type '{:s}' the top {:d} values cover {:.0%} of uses".format(attr_type,i,prop)
                return i
            if i >= maxcount:
                print "for type '{:s}' the top {:d} values do not cover {:.0%} of uses".format(attr_type,maxcount,prop)
                return None



def number_of_values_per_type(args, db_driver):
    print "generating spreadsheet with number of values for each attribute type"
    try:
        os.makedirs("neo4j-analysis/csv")
    except OSError:
        pass
    with open("neo4j-analysis/csv/num_values_distribution.csv", "w") as fileout:
        csvout = csv.writer(fileout)

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
                #print "%s, %d, %d, %.2f" % record_tuple
                values.append(record_tuple)
                csvout.writerow([x for x in record_tuple])
        attr_types, n_values, n_samples, ratios = map(list, zip(*values))
        counts = np.bincount(n_values)
        stats = {"mean": np.mean(n_values), "median": np.median(n_values), "mode": np.argmax(counts)}

        print "Mean: %d" % (stats["mean"])
        print "Median: %d" % (stats["median"])
        print "Mode: %d" % (stats["mode"])

        fig = matplotlib.pyplot.figure(figsize=(24,18))

        ax1 = fig.add_subplot(211)
        ax1.bar(np.arange(len(n_values)), n_values,align="center")
        ax1.set_yscale("log")
        ax1.set_xticks(np.arange(len(n_values)))
        ax1.set_ylabel("Number of attribute values")

        ax2 = fig.add_subplot(212)
        ax2.bar(np.arange(len(n_values)), ratios,align="center")
        ax2.set_xticks(np.arange(len(n_values)))
        ax2.set_xticklabels(attr_types, rotation=90)
        ax2.set_xlabel("Attribute types")
        ax2.set_ylabel("Diversity of values")

        try:
            os.makedirs("neo4j-analysis/plot")
        except OSError:
            pass
        fig.savefig("neo4j-analysis/plot/value-diversity.png",bbox_inches='tight')


def new_test_function(args, db_driver, attr_type, usage_count):
    """
    Find the % of values for which the attribute type is actually a parent ontology term
    :param args:
    :param db_driver:
    :param attr_type:
    :param usage_count:
    :return:
    """

    print "getting percentage"
    max_words = 1000
    with db_driver.session() as session:
        cypher = \
            "MATCH (s:Sample)-->(a:Attribute{type:'{}')-[:hasIri]->(o:OntologyTerm)-[:inEfo]->(feo:EfoOntologyTerm)-[*]->(eo:EfoOntologyTerm) " \
            "WHERE LOWER(a.type) = LOWER(eo.label) " \
            "RETURN COUNT(s)" \
            "LIMIT {:d}".format(attr_type, max_words)

        results = session.run(cypher)


# def attribute_values_matching_efo_label(args, db_driver, attr_type, usage_count ):
#     print "generating value matching to efo label spreadsheet"
#     max_words = 1000
#     with db_driver.session() as session2:
#         cypher = \
#             "MATCH (s:Sample)-[:hasAttribute]->(a:Attribute{type: '{}'})-->(o:OntologyTerm) WITH s,a,o \
#             MATCH (eo:EfoOntologyTerm)<--(o)<--(a)-->(av:AttributeValue) \
#             WHERE eo.label <> av.name \
#             RETURN eo.label AS label, av.name AS attr_value, COUNT(s) AS sample_count \
#             ORDER BY sample_count DESC \
#             LIMIT {}".format(attr_type,max_words)
#
#         try:
#             os.makedirs("neo4j-analysis/csv")
#         except OSError:
#             pass
#
#         with open("neo4j-analysis/csv/{}_efo_label_matching.csv".format(attr_type), "w") as outfile:
#             csvout = csv.writer(outfile)
#
#             for attr in common:
#                 row = ["{} ({})".format(attr[0], attr[1])]
#
#                 with db_driver.session() as session2:
#                     cypher = "MATCH (s:Sample)-[u:hasAttribute]->(a:Attribute)-->(t:AttributeType{name:'"+attr[0]+"'}), \
#                               (a:Attribute)-->(v:AttributeValue) \
#                               RETURN v.name AS value, COUNT(u) AS usage_count ORDER BY usage_count DESC LIMIT 10"
#                     results2 = session2.run(cypher)
#                     for result2 in results2:
#                         row.append("{} ({})".format(result2["value"], result2["usage_count"]))
#
#                 csvout.writerow(row)


# def perc_sample_mapped_to_efo(args, db_driver, attr_type, usage_count):
#     print 'Generating csv file with percentage of attributes values mapped to EFO'
#     with db_driver.session() as session2:
#         cypher = 'MATCH (s:Sample'


if __name__ == "__main__":

    print "Welcome to the BioSamples analysis"

    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', default="neo4j-server-local")
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--wordcloud-entries',  type=int, default=1000)
    parser.add_argument('--top-attr',  type=int, default=0)
    parser.add_argument('--attr', action='append')

    args = parser.parse_args()

    driver = GraphDatabase.driver("bolt://"+args.hostname)

    print "Generation of reports started"

    # spreadsheet of most common attribute types and values
    if args.summary:
        generate_summary(args, driver)

    attrs = get_most_common_attributes(driver, args.top_attr)
    if args.attr != None:
		for attr in args.attr:
			usage_count = get_usage_count(driver, attr)
			attrs.append((attr, usage_count))

    for attr_type, usage_count in attrs:
        #generate_wordcloud_of_attribute(args, driver, attr_type,usage_count)
        attribute_value_mapped(args, driver, attr_type,usage_count)
        attribute_value_mapped_label_match(args, driver, attr_type,usage_count)
        #attribute_value_coverage(args, driver, attr_type, usage_count, 0.50, 100)
        #attribute_value_coverage(args, driver, attr_type, usage_count, 0.75, 250)
        #attribute_value_coverage(args, driver, attr_type, usage_count, 0.95, 500)
        

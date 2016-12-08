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
from neo4j.v1 import GraphDatabase, basic_auth

matplotlib.use('Agg')
import matplotlib.pyplot
import re


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

    with open(args.path+"/attr_common.csv", "w") as outfile:
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
    fig.savefig(args.path+"/freq-of-number-attrs.png", bbox_inches='tight')

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
        os.makedirs(args.path+"/word_clouds")
    except OSError:
        pass
    wc.to_file(args.path+"/word_clouds/cloud-types.png")
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
        results2 = session2.run(cypher, {"attr_type":attr_type, "max_words":max_words})
        for result2 in results2:
            freq2.append((result2["value"], result2["usage_count"]))
    wc = wordcloud.WordCloud(width=640, height=512, scale=2.0, max_words=max_words).generate_from_frequencies(freq2)
    wc.recolor(color_func=grey_color_func, random_state=3)
    try:
        os.makedirs(args.path+"/word_clouds")
    except OSError:
        pass
    wc.to_file(args.path+"/word_clouds/cloud-values-{:07d}-{}.png".format(usage_count,attr_type))
    print "generated wordcloud of values of", attr_type


def attribute_value_mapped(args, db_driver, attr_type, usage_count):
    cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}}) " \
             "RETURN COUNT(u) AS usage_count, COUNT(a.iri) AS mapped "
    with db_driver.session() as session:
        result = session.run(cypher, {"attr_type": attr_type})
        for record in result:
            prop = float(record["mapped"]) / float(usage_count)
            print "for type '{:s}' ontologies terms are mapped for {:.0%} of uses".format(attr_type, prop)
            return prop


def attribute_value_mapped_label_match(args, db_driver, attr_type, usage_count):
    cypher = 'MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}})-->(:OntologyTerm)-->(eo:OLS) \
        WHERE eo.label = a.value OR a.value IN eo.`synonyms[]`\
        RETURN COUNT(u) AS label_match_count'
    with db_driver.session() as session:
        result = session.run(cypher, {"attr_type": attr_type})
        for record in result:
            prop = float(record["label_match_count"]) / float(usage_count)
            print "for type '{:s}' ontologies terms have the same value for {:.0%} of uses".format(attr_type, prop)
            return prop


def attribute_value_coverage(args, db_driver, attr_type, usage_count, prop, maxcount):

    with db_driver.session() as session:
        cypher = "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}}) \
            RETURN a.value, count(u) AS count_s \
            ORDER BY count(u) DESC \
            LIMIT {maxcount}"
        result = session.run(cypher, {"attr_type":attr_type, "maxcount":maxcount})
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
        os.makedirs(args.path)
    except OSError:
        pass
    with open(args.path+"/num_values_distribution.csv", "w") as fileout:
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
        fig.savefig(args.path+"/value-diversity.png", bbox_inches='tight')


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
    prop = float(count) / float(usage_count)
    print "for type '{:s}' ontologies terms are a child term for {:.0%} of uses".format(attr_type, prop)


def attribute_value_mapped_obsolete(args, db_driver, attr_type, usage_count):
    total = 0
    with db_driver.session() as session:
        cypher = \
            "MATCH (:Sample)-[u:hasAttribute]->(a:Attribute{type:{attr_type}})" \
            "-->(o:OntologyTerm)-->(efo:OLS{obsolete:'True'}) " \
            "RETURN DISTINCT a.value AS value, COUNT(u) AS count, o.iri AS iri"
        results = session.run(cypher, {"attr_type": attr_type})
        for record in results:
            total += record["count"]

    prop = float(total) / float(usage_count)
    print "for type '{:s}' ontologies terms are obsolete for {:.0%} of uses".format(attr_type, prop)

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
#             csvout = unicodecsv.writer(outfile)
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

if __name__ == "__main__":
    print "Welcome to the BioSamples analysis"

    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', default="neo4j-server-local")
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--wordcloud-entries', type=int, default=1000)
    parser.add_argument('--top-attr', type=int, default=0)
    parser.add_argument('--attr', action='append')
    parser.add_argument('--path', default="out")

    args = parser.parse_args()

    driver = GraphDatabase.driver("bolt://" + args.hostname)

    print "Generation of reports started"

    # spreadsheet of most common attribute types and values
    if args.summary:
        generate_summary(args, driver)

    attrs = get_most_common_attributes(driver, args.top_attr, force=False)
    if args.attr is not None:
        for attr in args.attr:
            usage_count = get_usage_count(driver, attr)
            attrs.append((attr, usage_count))

    for attr_type, usage_count in attrs:
        generate_wordcloud_of_attribute(args, driver, attr_type, usage_count)
        attribute_value_mapped(args, driver, attr_type, usage_count)
        attribute_value_mapped_label_match(args, driver, attr_type, usage_count)
        attribute_value_mapped_obsolete(args, driver, attr_type, usage_count)
        attribute_value_coverage(args, driver, attr_type, usage_count, 0.50, 100)
        attribute_value_coverage(args, driver, attr_type, usage_count, 0.75, 250)
        attribute_value_coverage(args, driver, attr_type, usage_count, 0.95, 500)
        
        #attribute_value_child_of_type(args, driver, attr_type, usage_count, iri)

import os
import sys
import json
import re
import requests
import unicodecsv
import inflection
import argparse

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


class Annotation:
    def __init__(self, accession, attribute_type, attribute_value, ontology_term):
        self.accession = accession
        self.attributeType = attribute_type
        self.attributeValue = attribute_value
        self.ontologyTerm = ontology_term

    def __str__(self):
        try:
            return 'Annotation:{accession=\'' + self.accession + '\',\'' + self.attributeType + '\'=\''\
                   + self.attributeValue + '\',ontologyTerm=\'' + self.ontologyTerm + '\'}'
        except UnicodeDecodeError:
            print "Something went wrong handling sample " + self.accession


def count_results(content):
    return content['response']['numFound']


def convert(name):
    #given a string like "geographicLocation" return "Geographic Location"
    
    spaced = True
    out = ""
    for c in name:
        if spaced:
            out = out + c.upper()
            spaced = False
        elif c.isupper():
            out = out + " " +c.upper()
        else:
            out = out + c
            
    return out
    
    #return inflection.titleize(name)


def parse_response(content):
    results = []
    docs = content['response']['docs']
    for doc in docs:
        accession = doc['accession'].encode('utf-8')
        for key in doc:
            if key.encode('utf-8').endswith("_crt_json"):
                # remove postamble '_crt_json' from key and capitaliza/whitespace
                attribute_type = convert(key.encode('utf-8').replace("_crt_json",""))
                #print accession, key, attribute_type

                # unpack attribute value and ontology terms
                attribute_contents = doc[key]
                for attribute_content in attribute_contents:
                    annotation = ""
                    attribute_value_obj = json.loads(attribute_content.encode('utf-8'))
                    attribute_value = attribute_value_obj['text'].encode('utf-8')
                    if 'ontologyTerms' in attribute_value_obj.keys():
                        for ontology_term_obj in attribute_value_obj['ontologyTerms']:
                            ontology_term = ontology_term_obj.encode('utf-8')
                            annotation = Annotation(accession, attribute_type, attribute_value, ontology_term)
                    else:
                        annotation = Annotation(accession, attribute_type, attribute_value, "")
                    results.append(annotation)
    return results


def write_results(results, block):
    filename = "data/biosamples-annotations-" + str(block) + ".csv"
    
    filename = os.path.abspath(filename)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            writer = unicodecsv.writer(f, delimiter=',')
            writer.writerow(["ACCESSION", "ATTRIBUTE_TYPE", "ATTRIBUTE_VALUE", "ONTOLOGY_TERM"])

    with open(filename, 'a') as f:
        writer = unicodecsv.writer(f, delimiter=',')
        # print "Writing " + str(len(results)) + " annotations to " + filename
        for result in results:
            writer.writerow([result.accession, result.attributeType, result.attributeValue, result.ontologyTerm])


def usage():
    print "Run this script with -h (--help) or -n (--numberofrows) " \
          "to read out biosamples annotations, doing 'n' samples at each step"


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--numberofrows', '-n', type=int, default=1000)
    parser.add_argument('--startrow', '-s', type=int, default=0)
    parser.add_argument('--blocksize', '-b', type=int, default=100000)
    parser.add_argument('--hostname', default="cocoa.ebi.ac.uk:8989")
    args = parser.parse_args()


    baseurl = 'http://'+args.hostname+'/solr/samples/select?q=*%3A*&fl=accession%2C*_crt_json&wt=json&indent=true'

    print "Starting to evaluate annotations in BioSamples"
    print "base URL is "+baseurl
    print "starting from", args.startrow
    print "reading", args.numberofrows, "samples at a time from ", args.hostname
    print "writing ", args.blocksize, "samples per file"

    # Execute request to get documents
    initial_response = requests.get(baseurl)

    if initial_response.status_code == 200:
        total = count_results(json.loads(initial_response.content))

        print "Found " + str(total) + " sample documents in total"

    print "Exporting annotations from BioSamples " \
          "(fetching " + str(args.numberofrows) + " samples at a time, writing in blocks of " + str(args.blocksize) + ")"
    while args.startrow < total:
        if args.startrow % args.blocksize == 0:
            sys.stdout.write("\n")
            sys.stdout.write(str(args.startrow))
            sys.stdout.flush()
        block = (args.startrow / args.blocksize) + 1
        request_url = baseurl + '&start=' + str(args.startrow) + '&rows=' + str(args.numberofrows)
        response = requests.get(request_url)
        if response.status_code == 200:
            content = json.loads(response.content)
            results = parse_response(content)
            write_results(results, block)
            sys.stdout.write(".")
            sys.stdout.flush()
        args.startrow += args.numberofrows

    print "All done!"


if __name__ == "__main__":
    main(sys.argv[1:])

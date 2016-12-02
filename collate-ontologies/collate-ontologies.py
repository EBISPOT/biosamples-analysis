# pip install requests unicodecsv
import os
import sys
import argparse
import json

import requests
import unicodecsv

from requests_futures.sessions import FuturesSession


class OntologyTerm:
    def __init__(self, iri, label, synonyms, parents, is_obsolete):
        self.iri = iri
        self.label = label
        self.synonyms = synonyms
        self.is_obsolete = is_obsolete
        self.parents = parents


def write_results(results, ontology, term_writer, parent_writer):
    for result in results:
        term_writer.writerow([result.iri, result.label, ";".join(result.synonyms), ";".join(result.parents), result.is_obsolete])
        for parent in result.parents:
            parent_writer.writerow([result.iri, parent])


def get_parents(term_content):
    parents = []
    if "hierarchicalParents" in term_content["_links"]:
        parent_url = term_content["_links"]["hierarchicalParents"]["href"]
        pres = requests.get(parent_url)

        if pres.status_code == 200:
            content = pres.json()
            total_pages = content["page"]["totalPages"]
            # n_parent = 0
            # total_parents = content["page"]["totalElements"]

            for n_page in xrange(0,total_pages):
                parent_page_url = "{}?page={:d}".format(parent_url, n_page)
                pres = requests.get(parent_page_url)
                if pres.status_code == 200:
                    content = json.loads(pres.content)
                    terms = content["_embedded"]["terms"]
                    for term in terms:
                        parents.append(term["iri"].encode("utf-8"))
                n_page += 1
    return parents


def get_url(kargs):
    return "http://{hostname}/api/ontologies/{ontology}/terms?page={page}&size={size}".format(**kargs)

def bg_cb(sess, resp):
    # parse the json storing the result on the response object
    resp.data = resp.json()

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", "-o", type=str, default="efo")
    parser.add_argument("--page", "-p", type=int, default=0)
    parser.add_argument("--size", "-s", type=int, default=1000)
    parser.add_argument("--hostname", default="www.ebi.ac.uk/ols")
    args = parser.parse_args()

    nav_options = vars(args)
    check_url = get_url(nav_options)
    
    #get an intial URL to get total pages
    initial_response = requests.get(check_url)
    if initial_response.status_code != 200:
        print "Problem getting initial page"
        return
    content = json.loads(initial_response.content)
    total_pages = content["page"]["totalPages"]
    total_elements = content["page"]["totalElements"]
    n_element = (args.page * args.size)
    print "Total number of elements {:d}; Starting from element {:d}".format(total_elements, n_element)
        
    #now we can create the writers to handle output
    term_file = "data/tmp_{}_terms.csv".format(args.ontology)
    term_file = os.path.abspath(term_file)
    if not os.path.exists(os.path.dirname(term_file)):
        os.makedirs(os.path.dirname(term_file))
    
    parent_file = "data/tmp_{}_parents.csv".format(args.ontology)
    parent_file = os.path.abspath(parent_file)
    if not os.path.exists(os.path.dirname(parent_file)):
        os.makedirs(os.path.dirname(parent_file))

    #open the writers
    term_fieldnames = ["iri:ID(EfoOntologyTerm)", "label", "synonyms[]", "parents[]", "obsolete"]
    parent_fieldnames = [":START_ID(EfoOntologyTerm)", ":END_ID(EfoOntologyTerm)"]
    with open(term_file, 'w') as term_writer:
        term_writer = unicodecsv.writer(term_writer, delimiter=",")
        term_writer.writerow(term_fieldnames)
        with open(parent_file, 'w') as parent_writer:
            parent_writer = unicodecsv.writer(parent_writer, delimiter=",")
            parent_writer.writerow(parent_fieldnames)
        
            #prepare for asynchronisity
            session = FuturesSession(max_workers=25)
            futures = []
        
            #now get each page and parse it
            for page_i in xrange(args.page, total_pages):
                nav_options["page"] = page_i
                page_url = get_url(nav_options)

                futures.append(session.get(page_url, background_callback=bg_cb))
                
            for future in futures:
                res = future.result()
                content = res.data
                if res.status_code != 200:
                    print "Problem getting", page_url
                    return

                #loop over each term on the page
                terms = content["_embedded"]["terms"]
                results = []
                for term in terms:
                    n_element += 1
                    iri = term["iri"].encode("utf-8")
                    if term["synonyms"]:
                        synonyms = [s.strip().encode("utf-8") for s in term["synonyms"]]
                    else:
                        synonyms = []

                    label = term["label"].encode("utf-8").strip()
                    is_obsolete = term["is_obsolete"]
                    #call out to get all the parent term pages too
                    term_parents = get_parents(term)

                    ontology_term = OntologyTerm(iri=iri, synonyms=synonyms, label=label,
                                                 is_obsolete=is_obsolete, parents=term_parents)
                    results.append(ontology_term)
                    if n_element % 100 == 0:
                        print "Page {:d}/{:d} - Element {:d}/{:d}".format(nav_options["page"],
                                                                          total_pages,
                                                                          n_element,
                                                                          total_elements)

                    write_results(results, nav_options["ontology"], term_writer, parent_writer)

    print "\nProcess finished"

if __name__ == "__main__":
    main(sys.argv[1:])

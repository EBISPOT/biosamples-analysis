# pip install requests unicodecsv
import os
import sys
import argparse

import requests
import unicodecsv
import concurrent.futures


class OntologyTerm:
    def __init__(self, iri, label, synonyms, parents, is_obsolete):
        self.iri = iri
        self.label = label
        self.synonyms = synonyms
        self.is_obsolete = is_obsolete
        self.parents = parents



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

            for n_page in range(0,total_pages):
                parent_page_url = "{}?page={:d}".format(parent_url, n_page)
                pres = requests.get(parent_page_url)
                if pres.status_code == 200:
                    content = pres.json()
                    terms = content["_embedded"]["terms"]
                    for term in terms:
                        parents.append(term["iri"])
                n_page += 1
    return parents


def get_url(kargs):
    return "http://{hostname}/api/ontologies/{ontology}/terms?page={page}&size={size}".format(**kargs)

    
def handle_url(url):
    print("Handling url", url)
    results = []
    result = requests.get(url)
    if result.status_code != 200:
        print("Problem getting", page_url)
    else:    
        #loop over each term on the page
        terms = result.json()["_embedded"]["terms"]
        for term in terms:
            iri = term["iri"]
            if term["synonyms"]:
                synonyms = [s.strip() for s in term["synonyms"]]
            else:
                synonyms = []

            label = term["label"].strip()
            is_obsolete = term["is_obsolete"]
            
            #call out to get all the parent term pages too
            term_parents = get_parents(term)

            ontology_term = OntologyTerm(iri=iri, synonyms=synonyms, label=label,
                                         is_obsolete=is_obsolete, parents=term_parents)
            results.append(ontology_term)
    print("Handled url", url)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", "-o", type=str, default="efo")
    parser.add_argument("--page", "-p", type=int, default=0)
    parser.add_argument("--size", "-s", type=int, default=1000)
    parser.add_argument("--hostname", default="www.ebi.ac.uk/ols")
    parser.add_argument("--threads", type=int,default=4)
    args = parser.parse_args()

    nav_options = vars(args)
    check_url = get_url(nav_options)
    
    #get an intial URL to get total pages
    initial_response = requests.get(check_url)
    if initial_response.status_code != 200:
        print("Problem getting initial page")
    else:    
        content = initial_response.json()
        total_pages = content["page"]["totalPages"]
        total_elements = content["page"]["totalElements"]
        n_element = (args.page * args.size)
        print("Total number of pages {:d}".format(total_pages))
            
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
        with open(term_file, 'wb') as term_writer:
            term_writer_csv = unicodecsv.writer(term_writer, delimiter=",")
            term_writer_csv.writerow(['iri:ID({}OntologyTerm)'.format(args.ontology), 'label', 'synonyms[]', 'parents[]', 'obsolete'])
            with open(parent_file, 'wb') as parent_writer:
                parent_writer_csv = unicodecsv.writer(parent_writer, delimiter=",")
                parent_writer_csv.writerow([':START_ID({}OntologyTerm)'.format(args.ontology), ':END_ID({}OntologyTerm)'.format(args.ontology)])
            
                #prepare for asynchronisity
                with concurrent.futures.ProcessPoolExecutor(max_workers = args.threads) as executor:
                    futures = []
                
                    #now get each page and parse it
                    for page_i in range(args.page, total_pages):
                        nav_options["page"] = page_i
                        page_url = get_url(nav_options)
                        future = executor.submit(handle_url, page_url)
                        futures.append(future)
                        
                    for future in futures:
                        for ontology_term in future.result():
                            synonyms = ';'.join(ontology_term.synonyms)
                            parents = ';'.join(ontology_term.parents)
                            term_writer_csv.writerow([ontology_term.iri, ontology_term.label, synonyms, parents, ontology_term.is_obsolete])
                            for parent in ontology_term.parents:
                                parent_writer_csv.writerow([ontology_term.iri, parent])

    print("\nProcess finished")

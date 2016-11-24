# pip install requests unicodecsv
import os
import sys
import requests
import argparse
import unicodecsv
import json


class OntologyTerm:
	def __init__(self, iri, label, synonyms, parents, is_obsolete):
		self.iri = iri
		self.label = label
		self.synonyms = synonyms
		self.is_obsolete = is_obsolete
		self.parents = parents


def write_results(results, block, ontology):
	term_file = "data/{}-terms-{:03d}.csv".format(ontology, block)
	parent_file = "data/{}-parents-{:03d}.csv".format(ontology, block)

	term_file = os.path.abspath(term_file)
	parent_file = os.path.abspath(parent_file)
	if not os.path.exists(os.path.dirname(term_file)):
		os.makedirs(os.path.dirname(term_file))

	if not os.path.exists(term_file):
		with open(term_file, 'w') as f:
			term_writer = unicodecsv.writer(f, delimiter=",")
			term_writer.writerow(["iri:ID(EfoOntologyTerm)", "label", "synonyms[]", "parents[]", "obsolete"])
	if not os.path.exists(parent_file):
		with open(parent_file, 'w') as f:
			parent_writer = unicodecsv.writer(f, delimiter=",")
			parent_writer.writerow([":START_ID(EfoOntologyTerm)", ":END_ID(EfoOntologyTerm)"])

	with open(term_file, 'a') as f:
		with open(parent_file, 'a') as p:
			term_writer = unicodecsv.writer(f, delimiter=",")
			parent_writer = unicodecsv.writer(p, delimiter=",")
			for result in results:
				term_writer.writerow([result.iri, result.label, ";".join(result.synonyms), ";".join(result.parents), result.is_obsolete])
				for parent in result.parents:
					parent_writer.writerow([result.iri, parent])


def get_parents(term_content):
	parents = []
	if "hierarchicalParents" in term_content["_links"]:
		parent_url = term_content["_links"]["hierarchicalParents"]["href"]
		print parent_url
		pres = requests.get(parent_url)

		if pres.status_code == 200:
			content = json.loads(pres.content)
			n_page = 0
			total_pages = content["page"]["totalPages"]
			# n_parent = 0
			# total_parents = content["page"]["totalElements"]

			while n_page < total_pages:
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


def main(argv):
	parser = argparse.ArgumentParser()
	parser.add_argument("--ontology", "-o", type=str, default="efo")
	parser.add_argument("--page", "-p", type=int, default=0)
	parser.add_argument("--size", "-s", type=int, default=1000)
	parser.add_argument("--blocksize", "-b", type=int, default=10000)
	parser.add_argument("--hostname", default="www.ebi.ac.uk/ols")
	args = parser.parse_args()

	nav_options = vars(args)
	check_url = get_url(nav_options)

	initial_response = requests.get(check_url)
	if initial_response.status_code == 200:
		content = json.loads(initial_response.content)
		total_pages = content["page"]["totalPages"]
		total_elements = content["page"]["totalElements"]
		n_element = (args.page * args.size)
		print "Total number of elements {:d}; Starting from element {:d}".format(total_elements, n_element)

		while nav_options["page"] < total_pages:
			page_url = get_url(nav_options)

			res = requests.get(page_url)
			content = json.loads(res.content)
			if res.status_code == 200:

				block = (n_element / args.blocksize) + 1
				terms = content["_embedded"]["terms"]
				results = []
				for term in terms:
					n_element += 1
					iri = term["iri"].encode("utf-8")
					if term["synonyms"]:
						synonyms = [s.encode("utf-8") for s in term["synonyms"]]
					else:
						synonyms = []
					label = term["label"].encode("utf-8")
					is_obsolete = term["is_obsolete"]
					term_parents = get_parents(term)

					ontology_term = OntologyTerm(iri=iri, synonyms=synonyms, label=label,
					                             is_obsolete=is_obsolete, parents=term_parents)
					results.append(ontology_term)
					if n_element % 100 == 0:
						print "Page {:d}/{:d} - Element {:d}/{:d}".format(nav_options["page"],
						                                                  total_pages,
						                                                  n_element,
						                                                  total_elements)

				write_results(results, block, nav_options["ontology"])
			nav_options["page"] += 1
		print "Page {:d}/{:d} - Element {:d}/{:d}".format(nav_options["page"],
		                                                  total_pages,
		                                                  n_element-1,
		                                                  total_elements)

	print "\nProcess finished"

if __name__ == "__main__":
	main(sys.argv[1:])

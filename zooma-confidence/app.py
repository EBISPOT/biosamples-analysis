import argparse
import csv
import json
import requests


def get_zooma_annotations(pv, pt=None):
	base_api_url = "http://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate?"
	query_subpart = "propertyValue={:s}".format(pv)
	if pt is not None:
		query_subpart = query_subpart + "&propertyType={:s}".format(pt)
	query = base_api_url + query_subpart
	res = requests.get(query)
	if res.status_code == 200:
		content = json.loads(res.content)
	else:
		content = []
	return content

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('--file')
	parser.add_argument('--size', type=int,  default="10000")
	parser.add_argument('--offset', type=int, default=0)
	parser.add_argument('--path', default="out")

	args = parser.parse_args()

	# file_name = "out_{:d}_{:d}.txt".format(args.size, args.offset/args.size)

	# with open(args.path + "/{:s}".format(file_name), 'w') as fileout:
	with open("./" + args.file, 'r') as filein:
		csvreader = csv.DictReader(filein, ['value', 'type'])
		curr = 0
		total = 0
		num_high_confidence = 0
		done = False
		while not done:
			if curr < args.offset + 1:
				csvreader.next()
				curr += 1
			else:
				if total == args.size:
					done = True
				else:
					row = csvreader.next()
					annotations = get_zooma_annotations(pv=row['value'], pt=row['type'])
					if len(annotations) == 1:
						confidence = annotations[0]['confidence']
						if confidence == 'HIGH':
							num_high_confidence += 1
					total += 1

		print "{:d}".format(num_high_confidence)





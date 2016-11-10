import csv
import os


def clear_output_folder():
	dir_path = os.path.dirname(os.path.realpath(__file__))
	output_path = os.path.join(dir_path, "output")
	os.system("rm -f %s/*" % output_path)
	# for f in os.listdir(output_path):
	# 	try:
	# 		os.unlink(os.path.join(output_path, f))
	# 	except OSError as e:
	# 		print e


def get_files(mode="r"):
	samples_file = open("./output/tmp_samples.csv", mode)
	attributes_file = open("./output/tmp_attributes.csv", mode)
	types_file = open("./output/tmp_types.csv", mode)
	values_file = open("./output/tmp_values.csv", mode)
	ontology_file = open("./output/tmp_ontologies.csv", mode)
	has_attribute_file = open("./output/tmp_has_attributes.csv", mode)
	has_type_file = open("./output/tmp_has_type.csv", mode)
	has_value_file = open("./output/tmp_has_value.csv", mode)
	has_iri_file = open("./output/tmp_has_iri.csv", mode)
	all_files = [
		samples_file, attributes_file, types_file, values_file, ontology_file,
		has_attribute_file, has_type_file, has_value_file, has_iri_file
	]

	return {
		"samples": samples_file,
		"attributes": attributes_file,
		"types": types_file,
		"values": values_file,
		"ontologies": ontology_file,
		"has_attribute": has_attribute_file,
		"has_type": has_type_file,
		"has_value": has_value_file,
		"has_ontology": has_iri_file,
		"all": all_files
	}


if __name__ == "__main__":

	clear_output_folder()

	files = get_files("a")

	csv_samples_writer = csv.writer(files["samples"], delimiter=",")
	csv_attributes_writer = csv.writer(files["attributes"], delimiter=",")
	csv_types_writer = csv.writer(files["types"], delimiter=",")
	csv_values_writer = csv.writer(files["values"], delimiter=",")
	csv_ontology_writer = csv.writer(files["ontologies"], delimiter=",")
	csv_has_attribute_writer = csv.writer(files["has_attribute"], delimiter=",")
	csv_has_type_writer = csv.writer(files["has_type"], delimiter=",")
	csv_has_value_writer = csv.writer(files["has_value"], delimiter=",")
	csv_has_ontology_writer = csv.writer(files["has_ontology"], delimiter=",")

	# Write headers
	csv_samples_writer.writerow(["accession:ID(Sample)"])
	csv_attributes_writer.writerow(["attributeId:ID(Attribute)", "type", "value", "iri"])
	csv_types_writer.writerow(["attributeTypeId:ID(AttributeType)"])
	csv_values_writer.writerow(["attributeValueId:ID(AttributeValue)"])
	csv_ontology_writer.writerow(["ontologyIri:ID(OntologyTerm)"])
	csv_has_attribute_writer.writerow([":START_ID(Sample),:END_ID(Attribute)"])
	csv_has_type_writer.writerow([":START_ID(Attribute),:END_ID(AttributeType)"])
	csv_has_value_writer.writerow([":START_ID(Attribute),:END_ID(AttributeValue)"])
	csv_has_ontology_writer.writerow([":START_ID(Attribute),:END_ID(OntologyTerm)"])

	# Read annotations files and write output
	file_number = 1
	annotations_fields = ["accession", "attr_type", "attr_value", "onto_term"]
	with open("biosamples-annotations-%d.csv" % file_number, 'r') as f:
		csv_reader = csv.DictReader(f, delimiter=",", fieldnames=annotations_fields)
		csv_reader.next()  # skip first line
		for line in csv_reader:
			accession = line.get("accession")
			attr_type = line.get("attr_type")
			attr_value = line.get("attr_value")
			onto_term = line.get("onto_term")
			attr_key = "%s__%s__%s" % (attr_type, attr_value, onto_term)

			csv_samples_writer.writerow([accession])
			csv_attributes_writer.writerow([attr_key, attr_type, attr_value, onto_term])
			csv_types_writer.writerow([attr_type])
			csv_values_writer.writerow([attr_value])
			csv_ontology_writer.writerow([onto_term])
			csv_has_attribute_writer.writerow([accession, attr_key])
			csv_has_type_writer.writerow([attr_key, attr_type])
			csv_has_value_writer.writerow([attr_key, attr_value])
			csv_has_ontology_writer.writerow([attr_key, onto_term])

	for f in files["all"]:
		f.close()

	files = get_files()

	for f in files["all"]:
		f.seek(0)
		seen = set()
		old_name = f.name
		final_name = old_name.replace("tmp_", "")
		with open(final_name, "w") as out:
			for line in f:
				if line not in seen:
					out.write(line)
					seen.add(line)
		f.close()

	os.system("rm -f output/tmp_*.csv")









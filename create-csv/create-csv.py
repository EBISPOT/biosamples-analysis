import csv
import os

if __name__ == "__main__":

	print "CSV file creation process started\n"
	
	with open("/data/tmp_samples.csv", "w") as samples_file:
		with open("/data/tmp_attributes.csv", "w") as attributes_file:
			with open("/data/tmp_types.csv", "w") as types_file:
				with open("/data/tmp_values.csv", "w") as values_file:
					with open("/data/tmp_ontologies.csv", "w") as ontology_file:
						with open("/data/tmp_has_attribute.csv", "w") as has_attribute_file:
							with open("/data/tmp_has_type.csv", "w") as has_type_file:
								with open("/data/tmp_has_value.csv", "w") as has_value_file:
									with open("/data/tmp_has_iri.csv", "w") as has_iri_file:

										csv_samples_writer = csv.writer(samples_file, delimiter=",")
										csv_attributes_writer = csv.writer(attributes_file, delimiter=",")
										csv_types_writer = csv.writer(types_file, delimiter=",")
										csv_values_writer = csv.writer(values_file, delimiter=",")
										csv_ontology_writer = csv.writer(ontology_file, delimiter=",")
										csv_has_attribute_writer = csv.writer(has_attribute_file, delimiter=",")
										csv_has_type_writer = csv.writer(has_type_file, delimiter=",")
										csv_has_value_writer = csv.writer(has_value_file, delimiter=",")
										csv_has_ontology_writer = csv.writer(has_iri_file, delimiter=",")

										# Write headers
										csv_samples_writer.writerow(["accession:ID(Sample)"])
										csv_attributes_writer.writerow(["attributeId:ID(Attribute)", "type", "value", "iri"])
										csv_types_writer.writerow(["attributeTypeId:ID(AttributeType)"])
										csv_values_writer.writerow(["attributeValueId:ID(AttributeValue)"])
										csv_ontology_writer.writerow(["ontologyIri:ID(OntologyTerm)"])
										csv_has_attribute_writer.writerow([":START_ID(Sample)", ":END_ID(Attribute)"])
										csv_has_type_writer.writerow([":START_ID(Attribute)", ":END_ID(AttributeType)"])
										csv_has_value_writer.writerow([":START_ID(Attribute)", ":END_ID(AttributeValue)"])
										csv_has_ontology_writer.writerow([":START_ID(Attribute)", ":END_ID(OntologyTerm)"])

										# Read annotations files and write output
										annotations_fields = ["accession", "attr_type", "attr_value", "onto_term"]
										file_number = 1
										while os.path.isfile("/data/biosamples-annotations-%d.csv" % file_number):
											with open("/data/biosamples-annotations-%d.csv" % file_number, 'r') as f:
												print "Reading file #%d\n" % file_number
												csv_reader = csv.DictReader(f, delimiter=",", fieldnames=annotations_fields)
												csv_reader.next()  # skip first line because its the header
												for line in csv_reader:
													accession = line.get("accession")
													attr_type = line.get("attr_type")
													attr_value = line.get("attr_value")
													onto_term = line.get("onto_term")
													attr_key = "%s__%s__%s" % (attr_type, attr_value, onto_term)

													#check and filter out things with zero length
													#because they will break Neo4J import
													if len(attr_type.strip()) == 0:
														continue
													if len(attr_value.strip()) == 0:
														continue
													
													csv_samples_writer.writerow([accession])
													csv_attributes_writer.writerow([attr_key, attr_type, attr_value, onto_term])
													csv_types_writer.writerow([attr_type])
													csv_values_writer.writerow([attr_value])
													csv_has_attribute_writer.writerow([accession, attr_key])
													csv_has_type_writer.writerow([attr_key, attr_type])
													csv_has_value_writer.writerow([attr_key, attr_value])
													#ontology terms are optional
													if len(onto_term.strip()) != 0:
														csv_ontology_writer.writerow([onto_term])
														csv_has_ontology_writer.writerow([attr_key, onto_term])
														
											file_number += 1


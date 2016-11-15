from neo4j.v1 import GraphDatabase, basic_auth

import csv

import matplotlib
import wordcloud

#pip install neo4j-driver wordcloud matplotlib pillow 


if __name__ == "__main__":
	
	driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "password"))
	
	
	#spreadsheet of most common attribute types and values
	"""
	print "generating spreadsheet of most common attribute types and values"
	with open("attr_common.csv", "w") as outfile:
		csvout = csv.writer(outfile)
		
		with driver.session() as session:
			results = session.run("MATCH (s:Sample)-[:hasAttribute]->(:Attribute)-->(t:AttributeType) WITH t, COUNT(s) AS usage_count RETURN t.attributeTypeId as type, usage_count ORDER BY usage_count DESC LIMIT 100")
			for result in results:
				print "{} ({})".format(result["type"], result["usage_count"])
				
				row = ["{} ({})".format(result["type"], result["usage_count"])]
				
				
				with driver.session() as session2:
					cypher = "MATCH (s:Sample)-->(a:Attribute)-->(t:AttributeType{attributeTypeId:'"+str(result["type"])+"'}), (a:Attribute)-->(v:AttributeValue) WITH t,v,COUNT(s) AS usage_count RETURN t.attributeTypeId AS type, v.attributeValueId AS value, usage_count ORDER BY usage_count DESC LIMIT 10"
					print cypher
					results2 = session2.run(cypher)
					for result2 in results2:
						row.append("{} ({})".format(result2["value"], result2["usage_count"]))
						print "{} | {} ({})".format(result2["type"], result2["value"], result2["usage_count"])
						
				csvout.writerow(row)
				
	print "generated spreadsheet of most common attribute types and values"
	"""
	
	#wordcloud of most common attribute types and values
	print "generating wordcloud of most common attribute types and values"
	freq = []
	with driver.session() as session:
		results = session.run("MATCH (s:Sample)-[:hasAttribute]->(:Attribute)-->(t:AttributeType) WITH t, COUNT(s) AS usage_count RETURN t.attributeTypeId as type, usage_count ORDER BY usage_count DESC LIMIT 1000")
		i = 0
		for result in results:
			freq.append((result["type"],result["usage_count"]))
			if i < 25:
				i += 1
				print "generating wordcloud of values of",result["type"]
				freq2 = []
				with driver.session() as session2:
					cypher = "MATCH (s:Sample)-->(a:Attribute)-->(t:AttributeType{attributeTypeId:'"+str(result["type"])+"'}), (a:Attribute)-->(v:AttributeValue) WITH t,v,COUNT(s) AS usage_count RETURN t.attributeTypeId AS type, v.attributeValueId AS value, usage_count ORDER BY usage_count DESC LIMIT 1000"
					results2 = session2.run(cypher)
					for result2 in results2:
						freq2.append((result2["value"],result2["usage_count"]))
				wordcloud.WordCloud(width=640,height=512, scale=2.0,max_words=1000).generate_from_frequencies(freq2).to_file("cloud-values-{}.png".format(result["type"]))
				print "generated wordcloud of values of",result["type"]
		wordcloud.WordCloud(width=640,height=512, scale=2.0,max_words=1000).generate_from_frequencies(freq).to_file("cloud-types.png")
	print "generated wordcloud of most common attribute types and values"
		


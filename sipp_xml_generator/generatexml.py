import csv

def testttxgz():
	print ("test")
	return

def ReadCSV(input):
	sipp_msg_list = []
	with open(input, newline='') as csvfile:
		csv_reader = csv.reader(csvfile)
		for entry in csv_reader:
			sipp_msg_list.append(entry)
	return sipp_msg_list

def	GenerateXML(input_file, output_ifle):
	
	return True;


#!/usr/local/bin/python

import sys
import argparse
import csv

from generatexml import *

def ReadCSV(input):
	sipp_msg_list = []
	with open(input, newline='') as csvfile:
		csv_reader = csv.reader(csvfile)
		for entry in csv_reader:
			sipp_msg_list.append(entry)
	return sipp_msg_list

if __name__ == "__main__":
	# verify the python version. python3 is required.
	version_major = sys.version_info[0]
	if version_major != 3:
		glb.logger.error('Python 3 is required. Please check the python version and upgrade to python3. Programme exist!')
		sys.exit()

	parser = argparse.ArgumentParser(description='SIPP XML SCRIPTS Generator')
	parser.add_argument('--input', required = False, type = str, help = 'input csv file, defualt is input.csv', default = "input.csv")
	parser.add_argument('--output', required = False, type = str, help = 'output xml file, defualt is sipp.xml', default = "sipp.xml")

	args = parser.parse_args()

	input_file = args.input
	output_file = args.output
	if (output_file == 'sipp.xml' and input_file != 'input.csv'):
		output_file = input_file.split('.')[0] + '.xml'
	
	sip_msg_list = ReadCSV(input_file)
	GenerateXML(sip_msg_list, output_file)

	#glb.logger.info("ALL DONE !")

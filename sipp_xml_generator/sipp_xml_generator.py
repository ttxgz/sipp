import sys
import argparse
import csv

from generatexml import *

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
	
	print("aaaaa")
	testttxgz()
	b = ReadCSV(input_file)
	GenerateXML(glb.input_file, globals.output_ifle)

	glb.logger.info("ALL DONE !")
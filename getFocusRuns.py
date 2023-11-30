#!/usr/bin/env python3
import argparse, sys, json, datetime, os, re
import matplotlib.pyplot
import numpy
import focusData

		
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Plots the data in the CSV file.')
	parser.add_argument('-d', '--directory', default="/obsdata/whta/", type=str, help='Root folder for obsdata. Default is ''/obsdata/whta/''.')
	parser.add_argument('--limit', default=-1, type=int, help="Limit to the most recent 'n' nights. Default will retrieve all in the root folder.")
	args = parser.parse_args()
	
	folder = os.listdir(args.directory)
	
	folderList = []
	for f in folder:
		if re.search("[0-9]{8}", f): folderList.append(f)

	folderList.sort(reverse=True)
	if args.limit==-1:limit = args.limit
	else: limit = args.limit
	autoFocusList = []
	for index, folder in enumerate(folderList):
		if index==limit: break
		files = os.listdir(os.path.join(args.directory, folder))
		count = 0
		for f in files:
			if re.search("autofocus_log_[0-9]{8}", f): 
				autoFocusList.append(os.path.join(args.directory, folder, f))
				count+=1
		print("%d: scanning folder: %s   - found %d focus log files."%(index, folder, count))
		

	print(autoFocusList)

	# Write list of autofocus logs 
	output = open("autofocusruns.txt", "wt")
	for a in autoFocusList:
		output.write(a + "\n")
	output.close()

	focusData = focusData.focusData()
	for focus in autoFocusList:
		inputFile = open(focus, "rt")
		nightDate = re.search("[0-9]{8}", focus).group()
		print("Night:", nightDate)
		headers = ""
		for line in inputFile:
			if len(line)<1: continue
			if line[0]=='#': 
				headers+= line.strip()
				continue
			fields = line.strip().split(",")
			if "No data available" in fields[0]: continue
			if "Targ" in headers:
				focusData.addEntry(nightDate, fields, TargColumn = True)
			else: focusData.addEntry(nightDate, fields, TargColumn = False)
	
	# focusData.filterCamera("FPI")
	focusData.writeToJSON("allfocus.json")
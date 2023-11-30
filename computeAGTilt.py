#!/usr/bin/env python3
import argparse, sys, json, datetime, os, re
import matplotlib.pyplot
import numpy

class focusData:
	def __init__(self):
		self.data = []

	def addEntry(self, night, fields, TargColumn = True):
		print("fields:", fields)
		entry = { "night": night }
		offset = 0
		entry['RunID'] = fields[0].strip()
		if TargColumn: 
			entry['target'] = fields[1].strip()
		else:
			entry['target'] = ""
			offset = -1
		entry['UTFirst'] = fields[2 + offset].strip()
		entry['UTLast'] = fields[8 + offset].strip()
		entry['focusFirst'] = fields[7 + offset].strip()
		entry['focusLast'] = fields[13 + offset].strip()
		entry['RunFirst'] = fields[3 + offset].strip()
		entry['RunLast'] = fields[9 + offset].strip()
		entry['Alt'] = (float(fields[4 + offset].strip()) + float(fields[10 + offset].strip())) / 2
		try: entry['Rot'] = (float(fields[5 + offset].strip()) + float(fields[11 + offset].strip())) / 2
		except ValueError: return
		entry['Temp'] = (float(fields[6 + offset].strip()) + float(fields[12 + offset].strip())) / 2 
		try: entry['x'] = float(fields[14 + offset].strip())
		except ValueError: entry['x'] = -999
		try: entry['y'] = float(fields[15 + offset].strip())
		except ValueError: entry['y'] = -999
		entry['Camera'] = fields[16 + offset].strip()
		entry['Exptime'] = float(fields[17 + offset].strip())
		try: entry['focus'] = float(fields[18 + offset].strip())
		except ValueError: entry['focus'] = -999
		try: entry['FWHM'] = float(fields[19 + offset].strip())
		except ValueError: entry['FWHM'] = -999
		self.data.append(entry)
		print("added ", entry)

	def filterCamera(self, camera):
		newList = []
		for d in self.data:
			if d['Camera'] == camera: newList.append(d)
		self.data = newList

	def writeToCSV(self, filename):
		outputFile = open(filename, "wt")

		outputFile.write("# Night, RunID, UTstart, Camera, Temp, Alt, Rot, focus, FWHM, x, y, target\n")
		for line in self.data:
			if line['focus']==-999: continue
			outputFile.write("%s, %s, %s, %s, %.1f, %.1f, %.1f, %.3f, %.3f, %.3f, %.3f"%(line['night'], line['RunID'], line['UTFirst'], line['Camera'], line['Temp'], line['Alt'], line['Rot'], line['focus'], line['FWHM'], line['x'], line['y']))
			try: outputFile.write(", %s\n"%line['target'])
			except ValueError: outputFile.write("\n")

		outputFile.close()

		
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Calculates the tilt for eligible AG focus runs.')
	parser.add_argument("-f", "--focuslog", default="allfocus.csv", help="File containing a list of all focus runs.")
	parser.add_argument('-d', '--directory', default="/obsdata/whta/", type=str, help='Root folder for obsdata. Default is ''/obsdata/whta/''.')
	args = parser.parse_args()
	
	focusList = []
	headings = ""
	limit = 10
	counter = 0
	inputFile = open(args.focuslog, "rt")
	focuslogs = []
	
	for line in inputFile:
		counter+=1
		if counter==limit: break
		if len(line)<1: continue
		if line[0]=="#": 
			headings+=line
			continue
		
		fields = line.strip().split(',')
		camera = fields[4]
		if camera=="AGWEAVE": 
		print(fields)
		focuslogs.append(fields[0])
	
	print(nightlogs)
	inputFile.close()
	sys.exit()
	
	folder = os.listdir(args.directory)
	
	folderList = []
	for f in folder:
		if re.search("[0-9]{8}", f): folderList.append(f)

	folderList.sort(reverse=True)
	limit = 1E6
	autoFocusList = []
	for index, folder in enumerate(folderList):
		if index==limit: break
		print(index, folder)
		files = os.listdir(os.path.join(args.directory, folder))
		for f in files:
			if re.search("autofocus_log_[0-9]{8}", f): autoFocusList.append(os.path.join(args.directory, folder, f))

	print(autoFocusList)

	# Write list of autofocus logs 
	output = open("autofocusruns.txt", "wt")
	for a in autoFocusList:
		output.write(a + "\n")
	output.close()

	focusData = focusData()
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
	focusData.writeToCSV("allfocus.csv")
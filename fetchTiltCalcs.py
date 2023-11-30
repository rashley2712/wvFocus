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
	parser = argparse.ArgumentParser(description='Pulls the tilt data from Jure''s fits.')
	parser.add_argument('-d', '--directory', default="/home/whtobs/multifocus/", type=str, help='Root folder for fits. Default is ''/home/whtobs/multifocus/''.')
	args = parser.parse_args()
	

	folder = os.listdir(args.directory)
	
	calcList = []
	for f in folder:
		if re.search("fittingResult-[0-9]{8}T[0-9]{6}.txt", f): calcList.append(f)

	calcList.sort(reverse=True)
	print("found %d AGWEAVE focus runs to process."%len(calcList))


	tiltData = []
	for index in range(0, len(calcList)):
		dateTime = calcList[index][14:29]
		print(dateTime)

		# Load up all the focus runs.
		focusRuns = []
		focusFile = open('allfocus.csv')
		found = False
		for line in focusFile:
			fields = line.strip().split(',')
			if fields[1].strip() == dateTime: 
				focusInfo = fields
				found = True
				break
		focusFile.close()

		if not found: continue
		# Get the tilt value
		calcFile = open(os.path.join(args.directory, calcList[index]), "rt")
		for line in calcFile:
			#print(line)
			if "Tilt" in line:
				fields = line.split()
				#print(fields)
				tilt = float(fields[1])

		#print(focusInfo)
		temp = float(focusInfo[5])
		alt = float(focusInfo[6])
		print(dateTime, tilt, temp, alt)
		
		dataPoint = { "dateTime": dateTime, "tilt" : tilt, "temp" : temp, "alt" : alt}
		tiltData.append(dataPoint)

	# Plot tilt vs alt
	xData = [ f['alt'] for f in tiltData ]
	yData = [ f['tilt'] for f in tiltData ]
	print(xData, yData)


	matplotlib.pyplot.scatter(xData, yData)
	matplotlib.pyplot.xlabel("Altitude (deg)")
	matplotlib.pyplot.ylabel("Focus (mm)")
	
	matplotlib.pyplot.draw()
	matplotlib.pyplot.savefig("AGWEAVE_tilts.png")
	matplotlib.pyplot.show()


	sys.exit()
	focusList = []
	headings = ""
	limit = 10
	counter = 0
	inputFile = open(args.focuslog, "rt")
	focuslogs = []

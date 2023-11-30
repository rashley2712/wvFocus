import json, os


def checkFITSheaders(filename, header):
	headers = {}
	from astropy.io import fits
	try:
		hdulist = fits.open(filename)  # open the FITS file
	except FileNotFoundError:
		print("File not found: %s"%filename)
		return "not found" 
	hdr = hdulist[0].header  # the primary HDU header
	card = hdulist[0]
	for key in card.header.keys():
		headers[key] = card.header[key]
	hdulist.close(output_verify='ignore')

	try: return headers[header]
	except KeyError:
		return "not found"

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

	def getTargetsByRunID(self, runID): 
		runIDtargets = []
		for run in self.data:
			if run['RunID'] == runID: runIDtargets.append(run['target'])
		return runIDtargets

	def countFocusRuns(self, configuration):
		print("Counting focus runs for: %s"%configuration)
		runIDlist = []
		counter = 0
		for run in self.data:
			if run['RunID'] in runIDlist: continue

			runIDlist.append(run['RunID'])

			if configuration=="MOS":
				dataFolder = "/obsdata/whta/"
				firstFile = run['RunFirst']
				source = os.path.join(dataFolder, run['night'], "r%s.fit"%firstFile)
				#print(firstFile, source)
				plate = checkFITSheaders(source, "PLATE")
				#print(plate)
				if plate=="PLATE_A" or plate=="PLATE_B": counter+=1
		print("unique runids %d"%len(runIDlist))
		print("MOSA/B count: %d"%counter)

	def filterCamera(self, camera):
		newList = []
		for d in self.data:
			if d['Camera'] == camera: newList.append(d)
		self.data = newList

	def writeToCSV(self, filename):
		outputFile = open(filename, "wt")

		outputFile.write("# Night, RunID, RunFirst, RunLast, UTstart, Camera, Temp, Alt, Rot, focus, FWHM, x, y, target\n")
		for line in self.data:
			if line['focus']==-999: continue
			outputFile.write("%s, %s, %s, %s, %s, %s, %.1f, %.1f, %.1f, %.3f, %.3f, %.3f, %.3f"%(line['night'], line['RunID'], line['RunFirst'], line['RunLast'], line['UTFirst'], line['Camera'], line['Temp'], line['Alt'], line['Rot'], line['focus'], line['FWHM'], line['x'], line['y']))
			try: outputFile.write(", %s\n"%line['target'])
			except ValueError: outputFile.write("\n")
		outputFile.close()

	def pop(self):
		return self.data.pop(0)

	def writeToJSON(self, filename):
		outputFile = open(filename, "wt")
		json.dump(self.data, outputFile, indent=4)
		outputFile.close()


	def loadFromJSON(self, filename):
		inputfile = open(filename, "rt")
		self.data = json.load(inputfile)
		inputfile.close()

	def loadFromCSV(self, filename):
		inputFile = open(filename, "rt")
		for line in inputFile:
			print(line)

	def summary(self):
		summary =  "%d focus runs."%len(self.data)
		summary+="\n First 3 elements\n"
		for index in range(3):
			summary+= str(self.data[index]) + "\n"
		return summary
		
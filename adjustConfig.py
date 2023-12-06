#!/usr/bin/env python3
import argparse, sys, json, datetime, os, re, shutil, subprocess, time
import matplotlib.pyplot
import numpy
import focusData

		
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Adjusts the config to reflect the fibre positions on the date of the focus run.')
	parser.add_argument('rundate', type=str, help='Date-time of the focus run eg 20221130T223158.')
	parser.add_argument('plate', type=str, help='Plate (PLATEA or PLATEB)')
	args = parser.parse_args()
	workingPath = os.getcwd()
	plate = args.plate[0:5] + "_" + args.plate[5]
	
	configOriginal = "/wht/etc/wvautoguider.config"
	positionChanges = "FIBXchanges.dat"
	dataFolder = "/obsdata/whta/"
	
	focusRunDate = args.rundate
	
	try: 
		fibreChangesFile = open("FIBPXchanges.dat")
	except FileNotFoundError:
		try: 
			fibreChangesFile = open("../FIBPXchanges.dat")
		except FileNotFoundError:
			print("Can't find file with fibre position history. Exiting.")
			sys.exit(1)

	fibreChanges = []
	for line in fibreChangesFile:
		line = line.strip()
		fields = line.split()
		year = int(fields[1][0:4])
		month = int(fields[1][5:7])
		day = int(fields[1][8:10])
		hour = int(fields[2][0:2])
		minute = int(fields[2][3:5])
		second = float(fields[2][6:])
		timestamp = datetime.datetime(year = year, month=month, day=day, hour=hour, minute=minute, second=int(second))
		unixtime = time.mktime(timestamp.timetuple())
		fibreChange = { "timestamp" : timestamp, "plate" : fields[3], "unixtime": unixtime, "fields" : fields }
		fibreChanges.append(fibreChange)
	fibreChangesFile.close()
	
	year = int(focusRunDate[0:4])
	month = int(focusRunDate[4:6])
	day = int(focusRunDate[6:8])
	hour = int(focusRunDate[9:11])
	minute = int(focusRunDate[11:13])
	second = int(focusRunDate[13:15])
	print(focusRunDate, year, month, day, hour, minute, second)
	runDatetime = datetime.datetime(year, month, day, hour, minute, second)
	runUnixtime = time.mktime(runDatetime.timetuple())
	print("Run date: ", runDatetime, runUnixtime)

	latestChange = "none"
	for fibreChange in fibreChanges:
		if fibreChange['unixtime']<runUnixtime and fibreChange['plate'] == plate: latestChange = fibreChange
	print("Most recent change prior to this focus run is: ", latestChange)

	fields = latestChange['fields']
	fibresXY = []
	for index in range(4, 20, 2):
		fibresXY.append( ( fields[index], fields[index+1]))
	

	if plate=="PLATE_A": configLineString = "fibcen_mosa"
	else: configLineString = "fibcen_mosb"

	# Grab the default config file
	originalFile = open(configOriginal, "rt")
	outputFile = open("adjusted.config", "wt")
	for line in originalFile:
		newLine = line
		if configLineString in line:
			newLine = configLineString + " = ["
			for fibre in fibresXY:
				newLine+="'%s, %s', "%fibre
			newLine = newLine[:-2] + "]\n"
			print("modifying line in the config file from \n\t%s \nto \n\t%s"%(line, newLine))
		#print(line)
		outputFile.write(newLine)
	originalFile.close()
	outputFile.close()

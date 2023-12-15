#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan the given directory for directory names in form YYYYMMDD and
for directory get a list of FITS files with names like AG*.fit
For each files read the header and check for presence of keywords
with names FIBPX<n>X and FIBPX<n>Y, where <n> ranges between 1 and 8.
If the keywords are present, compare to previously stored values,
and if they different, print name of the file, date and time,
and the values of the keywords.
"""

import sys
import os
import argparse, datetime
import glob
from astropy.io import fits
import numpy as np

def getFibVals(fileName):
    """
    Read the FITS header from the given file and return a dictionary
    with values of keywords FIBPX<n>X and FIBPX<n>Y, where <n> ranges
    between 1 and 8.
    :param fileName: Name of the FITS file
    :return: Dictionary with values of keywords FIBPX<n>X and FIBPX<n>Y
    """

    # Open the file
    hdul = fits.open(fileName)
    # Get the header
    hdr = hdul[0].header
    # Get the values of the keywords
    fibVals = {}
    for i in range(1, 9):
        xKey = f"FIBPX{i}X"
        yKey = f"FIBPX{i}Y"
        if xKey in hdr and yKey in hdr:
            fibVals[xKey] = hdr[xKey]
            fibVals[yKey] = hdr[yKey]

    return fibVals


def parseArgs():
    """
    Parse the command line arguments.
    :return: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Scan the given directory for diretctory names in form YYYYMMDD and for directory get a list of FITS files with names like AG*.fit For each files read the header and check for presence of keywords with names FIBPX<n>X and FIBPX<n>Y, where <n> ranges between 1 and 8. If the keywords are present, compare to previously stored values, and if they different from the currently sdtored, print name of the file, date and time, and the values of the keywords.')
    parser.add_argument('dirName', type=str, help='Directory name')
    parser.add_argument('-o', '--output', default="FIBPXchanges.dat", type=str, help='Output file name', required=False)
    parser.add_argument('--full', action="store_true", help='Force a full rebuild of the output file, otherwise do an incremental build.', required=False)

    args = parser.parse_args()
    return args


def getDirNames(dirName, fromDate = datetime.datetime.strptime("2000-01-01", "%Y-%m-%d")):
    """
    Scan the given directory for subdirectories with names in form YYYYMMDD
    and return a list of such names.
    :param dirName: Name of the directory to scan
    :return: List of directory names
    """
    import os
    dirNames = []
    for name in os.listdir(dirName):
        if os.path.isdir(os.path.join(dirName, name)):
            if len(name) == 8 and name.isdigit():
                dirNames.append(name)

    # filter out dirnames older than fromDate
    newDirnames = []
    for d in dirNames:
        try:
            if datetime.datetime.strptime(d, "%Y%m%d") > fromDate:
                newDirnames.append(d)
        except ValueError:
            continue

    return newDirnames

def compareVals(currentVals, fibVals):
    """
    Given two dictionaries with values of keywords FIBPX<n>X and FIBPX<n>Y,
    where <n> ranges between 1 and 8, compare the values and return True
    if they are different, False otherwise.
    Consider the values different if the difference is larger than 1 in any coordinate.
    :param currentVals: Dictionary with current values
    :param fibVals: Dictionary with new values
    :return: True if the values are different, False otherwise
    """
    for key in fibVals:
        if key not in currentVals or abs(fibVals[key] - currentVals[key]) > 1:
            return True

    return False
    

def main():
    args = parseArgs()
    dirName = args.dirName
    outputFileName = args.output
    oldestDate = "2000-01-01"

    fullSearch = False
    mostRecentDatePlate = [ datetime.datetime.strptime("2000-01-01", "%Y-%m-%d"), datetime.datetime.strptime("2000-01-01", "%Y-%m-%d") ]
    if not args.full:   # Try to re-use an existing results file and only scan newer folders.
        try: 
            existingFile = open(outputFileName, "rt")
            for line in existingFile:
                fields = line.strip().split()
                lineDate = datetime.datetime.strptime(fields[1], "%Y-%m-%d")
                if fields[3]=="PLATE_A" and lineDate>mostRecentDatePlate[0]:
                    mostRecentDatePlate[0]=lineDate
                if fields[3]=="PLATE_B" and lineDate>mostRecentDatePlate[1]:
                    mostRecentDatePlate[1]=lineDate
            existingFile.close()
            if mostRecentDatePlate[0]<mostRecentDatePlate[1]: oldest = mostRecentDatePlate[0]
            else: oldest = mostRecentDatePlate[1]
            oldestDate = oldest.strftime("%Y-%m-%d")
            print("oldest entry is %s. Will scan from there..."%oldestDate)
            fullSearch = False
        except: 
            print("Could not find existing file %s with fibre positions. Will perform a full brute force search. Starting in 7 seconds. Ctrl-C to interrupt.")
            time.sleep(7)
            fullSearch = True
    else:
        fullSearch = True              


    currentVals = {'PLATE_A' : {}, 'PLATE_B' : {}}
    dailyNames = getDirNames(dirName, datetime.datetime.strptime(oldestDate,"%Y-%m-%d"))

    
    # Output file handle
    if outputFileName:
        if fullSearch: 
            outputFile = open(outputFileName, "wt")
        else:
            print("Appending to file %s"%outputFileName) 
            outputFile = open(outputFileName, "at")
    else:
        # Write to standard output
        outputFile = sys.stdout
    for dailyName in dailyNames:
        print(f"Processing {dailyName}")
        # Get the list of files
        fileNames = glob.glob(f"{dirName}/{dailyName}/ag*.fit")
        for fileName in fileNames:
            # Get the values of the keywords
            fibVals = getFibVals(fileName)
            # Get the plate name
            try:
                plate = fits.getval(fileName, "PLATE")
            except KeyError:
                # PLATE keyword not found
                continue

            if plate not in currentVals:
                # Unknown plate name
                continue

            try:
                guiSlide = fits.getval(fileName, "GUISLIDE")
                guidMode = fits.getval(fileName, "GUIDMODE")
                if guiSlide == 'PLATE_A' and guidMode != 'MOSA':
                    continue
                if guiSlide == 'PLATE_B' and guidMode not in ('MOSB', 'mIFU'):
                    continue
            except KeyError:
                # GUISLIDE or GUIDMODE keyword not found
                continue
            # Compare to the current values
            if compareVals(currentVals[plate], fibVals):
                # Extract values of DATE-OBS and UT from the header
                dateObs = fits.getval(fileName, "DATE-OBS")
                ut = fits.getval(fileName, "UT")
                # Strip the directory from the file name
                onlyName = os.path.basename(fileName)
                # Print the file name, date, time and the valueus to 3 decimal places (8.3f)
                print(f"{onlyName} {dateObs} {ut} {plate}", end='', file=outputFile, flush=True)
                for i in range(1, 9):
                    xKey = f"FIBPX{i}X"
                    yKey = f"FIBPX{i}Y"
                    if xKey in fibVals and yKey in fibVals:
                        print(f"{fibVals[xKey]:8.3f} {fibVals[yKey]:8.3f} ", end='', file=outputFile, flush=True)
                    else:
                        print("          ", end='', file=outputFile, flush=True)
                print(file=outputFile, flush=True)

                # Update the current values
                currentVals[plate].update(fibVals)


if __name__ == "__main__":
    main()
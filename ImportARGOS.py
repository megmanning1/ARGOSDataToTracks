##---------------------------------------------------------------------
## ImportARGOS.py
##
## Description: Read in ARGOS formatted tracking data and create a line
##    feature class from the [filtered] tracking points
##
## Usage: ImportArgos <ARGOS folder> <Output feature class> 
##
## Created: Fall 2024
## Author: meg.manning@duke.edu (for ENV859)
##---------------------------------------------------------------------

# Import packages
import sys, os, arcpy
arcpy.env.overwriteOutput = True

# Set input variables (Hard-wired)
inputFolder = arcpy.GetParameterAsText(0)   #'V:/ARGOSTracking/Data/ARGOSData'
outputFC = arcpy.GetParameterAsText(1)      #"V:/ARGOSTracking/Scratch/ARGOStrack.shp"
outputSR = arcpy.GetParameterAsText(2)      #arcpy.SpatialReference(54002)  #create a spatial reference to input into new feature class

## Prepare a new feature class to which we'll add tracking points
# Create an empty feature class; requires the path and name as separate parameters
outPath,outName = os.path.split(outputFC)
arcpy.CreateFeatureclass_management(outPath,outName,"POINT","","","",outputSR)

# Add TagID, LC, IQ, and Date fields to the output feature class
arcpy.management.AddField(outputFC,"TagID","LONG")
arcpy.management.AddField(outputFC,"LC","TEXT")
arcpy.management.AddField(outputFC,"Date","DATE")
#add file name as new attribute
arcpy.management.AddField(outputFC,"FileName","TEXT")

# Create the insert cursor --> places a lock on the file
cur = arcpy.da.InsertCursor(outputFC,['Shape@','TagID','LC','Date']) #'FileName'])

# iterate through files in the folder
for inputFile in os.listdir(inputFolder): 
    #Skip the README file
    if inputFile == "README.txt":
        continue

    #Get the file name without extension
    #fileName = os.path.splitext(inputFile)[0] ?

    # Construct a while loop to iterate through all lines in the datafile
    # Open the ARGOS data file for reading
    arcpy.addMessage(f"Working on file {inputFile}")
    inputFileObj = open(os.path.join(inputFolder, inputFile),'r')

    # Get the first line of data, so we can use a while loop
    lineString = inputFileObj.readline()

    # Start the while loop
    while lineString:
        
        # Set code to run only if the line contains the string "Date: "
        if ("Date :" in lineString):
            
            # Parse the line into a list
            lineData = lineString.split()
            
            # Extract attributes from the datum header line
            #modified to include Data, Time and LC
            tagID = lineData[0]
            obsDate = lineData[3]
            obsTime = lineData[4]
            obsLC = lineData[7]

            # Extract location info from the next line
            line2String = inputFileObj.readline()
            
            # Parse the line into a list
            line2Data = line2String.split()
            
            # Extract the date we need to variables
            obsLat = line2Data[2]
            obsLon= line2Data[5]
            
            #Try to convert the coordinates to numbers
            try:

                # Print results to see how we're doing
                print (tagID, obsDate, obsTime, obsLC, "Lat:"+obsLat,"Long:"+obsLon)

                # Convert raw coordinate strings to numbers
                if obsLat[-1] == 'N': #if it ends (-1) in N for north then make it a number and either make it negative for W or not
                    obsLat = float(obsLat[:-1])
                else:
                    obsLat = float(obsLat[:-1]) * -1
                if obsLon[-1] == 'E':
                    obsLon = float(obsLon[:-1])
                else:
                    obsLon = float(obsLon[:-1]) * -1

                # Construct a point object from the feature class
                obsPoint = arcpy.Point()
                obsPoint.X = obsLon
                obsPoint.Y = obsLat

                # Convert the point to a point geometry object with spatial reference
                inputSR = arcpy.SpatialReference(4326)
                obsPointGeom = arcpy.PointGeometry(obsPoint,inputSR)

                # Create a feature object
                feature = cur.insertRow((obsPointGeom,tagID,obsLC,obsDate.replace(".","/") + " " + obsTime))

            #Handle any error -_. just write out whatever you want
            except Exception as e:
                arcpy.AddWarning(f"Error adding record {tagID} to the output: {e}")
            
        # Move to the next line so the while loop progresses
        lineString = inputFileObj.readline()
        
    #Close the file object
    inputFileObj.close()

#Delete the cursor object
del cur

arcpy.AddMessage('All done!')


#Error handling - We should check CSV to make sure features exist

import os #operating system
cwd = os.getcwd() #get current working directory

import arcpy
import csv

# Display program purpose
print("California Home Natural Disaster Danger Index Calculator")
print("Use this program to calculate a Danger Index for Earthquake, Fire and Flood risk at your location(s) in California")
print()
print('************************************************************************************************') 
print()

# Kacy - Data Input
print("Please choose method of input: manual entry or by input file.")
inputSelection= str(input("\tEnter 'M' for manual or 'F' for file: "))

if inputSelection.upper() == "M":
    input_coordX = []        	
    input_coordY = []            

    while True:   
        coordX= float(input("\tEnter the X coordinate of the location: "))
        coordY= float(input("\tEnter the Y coordinate of the location: "))
        input_coordX.append(coordX)
        input_coordY.append(coordY)
        print()
        # determine whether user wants to enter another set of input values
        end = str(input("Do you want to stop entering values (Y/N)? "))
        print()
        if  end.upper() == 'Y' :
            break
    
    with open('coords.csv', 'w', newline='') as file:
        fwriter = csv.writer(file)
        fwriter.writerow(['x', 'y'])
        for iter in range(len(input_coordX)):
            fwriter.writerow([input_coordX[iter], input_coordY[iter]])

else:
    in_table = cwd + '/' + input('Please enter your coordinate CSV filename without extension: ') + ".csv"


print("Please weight the hazards. Allocate a percentage to each of the three hazards, totaling 100%")
while True:
    earthWeight= int(input("\tEarthquake Shaking Potential: "))
    fireWeight=  int(input("\tFire Hazard Severity Zone Rating: "))
    floodWeight= int(input("\tFlood Hazard: "))
    if earthWeight + fireWeight + floodWeight != 100:
        print("Weights entered do not add to 100, please enter different weights.")
    else:
        break

# for index in range(len(input_coordX)):         
#         print(input_coordX[index], "\t\t",input_coordY[index]) 



# Set environment settings
arcpy.env.workspace = cwd + r"\group4_psp.gdb"
arcpy.env.overwriteOutput = True

print(arcpy.ListFeatureClasses())

# Set Local Variables
# Set the local variables
x_coords = "x"
y_coords = "y"

point_feat = "testpoint"
out_feat = "pointrisks"

calipoly = 'CA_State_TIGER2016'
firepoly = 'CaliFireHazardSeverity'
floodpoly = 'CaliFloodHazardAreas'
quakepoly = 'EarthquakeRisk'

arcpy.management.XYTableToPoint(in_table, point_feat, x_coords, y_coords) # Create XY Event Layer

risks = [firepoly, quakepoly] # List of risks under consideration

interfeat = "in_memory/interfeat" #Feature for intermediate data

arcpy.analysis.Identity(point_feat, calipoly, interfeat, 'ONLY_FID') # Check if points are within California polygon

for risk in risks: #Iterate over points, intersect with each risk layer
    if risk == risks[-1]:
        arcpy.analysis.Identity(interfeat, risk, out_feat, 'NO_FID')
    else:
        arcpy.analysis.Identity(interfeat, risk, interfeat + '1', 'NO_FID')
        interfeat += '1'


arcpy.management.Delete("in_memory") #Clean-up intermediate layers

fields = arcpy.ListFields(out_feat)

print(arcpy.ListFeatureClasses())

for field in fields:
    print(field.name)

outfields = ['FID_testpoint', 'Shape@XY', 'FID_CA_State_TIGER2016', 'Haz_CODE', 'SA10_2_']

outpoints = []

with arcpy.da.SearchCursor(out_feat, outfields) as cursor:  #Iterate over output feature, pull relevant risk values for each point
    for row in cursor:
        outpoints.append(list(row))

# print(outpoints) - for testing

for point in outpoints:                                     # Make note of points not in California
    if point[2] == -1:
        point[3] = 'Not in California.'
        point[4] = ''
    else:                                                   # Calculate danger index value for points within California
        point[3] = round((float(point[3]) / 3) * 10)        # Converts fire risk value to value out of 10
        point[4] = round((float(point[4]) / 2.15) * 10)     # Converts earthquake risk value to value out of 10
        #point[5] Add Earthquake stuff here
        danger = ((point[3] * (fireWeight/100)) + (point[4] * (earthWeight) )) #+ (point[5] * (floodWeight)
        point.append(danger)
    point.pop(2)                                            # Remove california check field form list

# Delete output feature layer when data is extracted - UNCOMMMENT WHEN BUILD COMPLETE
arcpy.management.Delete(out_feat)

print(outpoints)
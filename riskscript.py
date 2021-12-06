#RiskScript.py
#Created By: Ridley Soudack, Jade Lacsamana, Kacy Hyndman, Kimberly Hansen
#Last Updated: December 5, 2021
#Calculates Danger Index for homes in California with reference to Earthquake, Fire, and Flood risks.
#Gets 1 or more x,y coordinates (meters) from either manual keyboard entry or .csv file, and weighting of each of the distaster variables via manual keyboard entry
#Uses arcpy processes to locate the coordinates with reference to vector data layers each with a hazard ranking that are then used in the weighted calculation for Danger Index
#Outputs displayed in .txt file and on screen

def pointidentity(incsv, workspace, polygonfcs, returnfields, spatialref, xycols=['x','y'], locationfeat=''):
    '''This function takes a CSV of x and y coordinates, optionally checks for their presence in an study area polygon, and then appends data to a list of their points
    based on their position within a series of supplied polygon feature classes.'''

    import arcpy
    # Set arcpy environment settings to local path + gdb location
    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True

    print(arcpy.ListFeatureClasses()) #For debugging, remove when done

    x_coords = xycols[0] # Set x and y coordinate columns from csv
    y_coords = xycols[1]

    inpoint = "inpoint" # Establish temporary layer names for in feature, intermediate feature, and out feature layers
    outpoint = "outpoint"
    interfeat = "in_memory/interpoint" # Set feature to hold temporary intermediate data

    arcpy.management.XYTableToPoint(incsv, inpoint, x_coords, y_coords, coordinate_system=spatialref) # Create XY Event Layer from CSV coordinates
    
    if locationfeat:
        arcpy.analysis.Identity(inpoint, locationfeat, interfeat, 'ONLY_FID') # If a location feature class has been supplied, check if points are within location polygon

    for risk in polygonfcs: # Iterate over points, intersect with each risk layer
        if risk == polygonfcs[-1]:
            arcpy.analysis.Identity(interfeat, risk, outpoint, 'NO_FID')
        else:
            arcpy.analysis.Identity(interfeat, risk, interfeat + '1', 'NO_FID')
            interfeat += '1'

    arcpy.management.Delete("in_memory") #Clean-up intermediate layers

    fields = arcpy.ListFields(outpoint) #For debugging

    print(arcpy.ListFeatureClasses()) #For debugging

    for field in fields: #For debugging
        print(field.name)

    outpoints = []
    with arcpy.da.SearchCursor(outpoint, returnfields) as cursor:  #Iterate over output feature, pull relevant risk values for each point
        for row in cursor:
            outpoints.append(list(row))
    
    arcpy.management.Delete(inpoint)
    arcpy.management.Delete(outpoint)

    return outpoints

def indexcalc(point, weights):
    '''Give a list, 'point', containing data for a point including standardized values for multiple criteria, and a separate list, 'weights' of weighting for each criteria (totalling 100), calculates an index based off of each criteria, redistributing weighting when criterion data not available.'''
    # Assumes that if a point has no data for a specific criteria, that criteria's value will equal -1, otherwise assumes criteria value are standardized.
    holdweight = 0 # Set variable to hold weight to be redistributed where values are empty
    for iter in range(len(point)):                              # Iterate over criteria values to check for any missing data, and add weighting for that missing data to holdweight to be redistributed
        if point[iter] == 0:
            holdweight+= weights[iter]
            weights[iter] = 0                                   # Set weight for missing data to 0
    denominator = len(weights) - weights.count(0)               # Calculate the number of criteria to redistribute weight into, then divides holdweight by that amount
    balance = holdweight/denominator
    index = 0
    for iter in range(len(weights)):                            # Redistribute leftover weight into weights for criteria which have data
        if weights[iter] != 0:
            weights[iter] += balance
        index += point[iter] * (weights[iter]/100)
    return index


def main():
    import os #operating system
    cwd = os.getcwd() #get current working directory

    import arcpy
    import csv

    # Display program purpose
    print("California Home Natural Disaster Danger Index Calculator")
    print("Use this program to calculate a Danger Index for Earthquake, Fire and Flood risk at your location(s) in California.")
    print("Assumptions: This program assumes that the locations entered that are within California are suitable or reasonable locations for a house to exist.")
    print()
    print('************************************************************************************************') 
    print()

    # Kacy - Data Input
    print("Please choose method of input: manual entry or by input file.")
    inputSelection= str(input("\tEnter 'M' for manual or 'F' for file: "))

    input_coordX = []        	
    input_coordY = []    

    if inputSelection.upper() == "M":       #Manual inputs section: gets x and y coordinates and appends to an empty list
            

        while True:   
            print("Please enter the location of this home in California (Teale) Albers (Meters) coordinates.")
            coordX= input("\tEnter the X coordinate of the location: ")
            coordY= input("\tEnter the Y coordinate of the location: ")
            coordX_sani = coordX.replace('.','').replace('-','') # Test to ensure coordinate values entered are numeric coordinates.
            coordY_sani = coordY.replace('.','').replace('-','')
            if (not coordX_sani.isdecimal()) or (not coordY_sani.isdecimal()): # Test to ensure coordinate values entered are numeric coordinates.
                print('Coordinate values may only contain digits 0-9, "." and "-".') # If values not acceptable, prompt user to re-enter and restart loop.
                print()
                print('Please enter your coordinates again.')
                print()
                continue
            input_coordX.append(coordX) # If coordinates are numeric, add to csv.
            input_coordY.append(coordY)
            print()
            # determine whether user wants to enter another set of input values. If not, loop ends
            end = str(input("Do you want to stop entering values (Y/N)? "))
            print()
            if  end.upper() == 'Y':
                break

    else:                   #File inputs sections: Reads a .csv file into the program for list of x,y coordinates
        while True:
            print()
            print('CSV should have header row, X coordinates in first column, Y coordinates in second column.') #Allowing user to upload a file without having to rename it
            in_table = cwd + '/' + input('Please enter your coordinate CSV filename without extension: ') + ".csv"
            if os.path.isfile(in_table): #Checks if file really exists and is CSV.
                with open(in_table) as filein:
                    inreader = csv.reader(filein)
                    next(inreader)  #Skip title row
                    rowskip = 0
                    for row in inreader:
                        coordX_sani = row[0].replace('.','').replace('-','')
                        coordY_sani = row[1].replace('.','').replace('-','')
                        if (not coordX_sani.isdecimal()) or (not coordY_sani.isdecimal()):  #Keeping track of any rows skipped due to improper type
                            rowskip += 1
                        else:
                            input_coordX.append(row[0])
                            input_coordY.append(row[1])
                print('File successfully read.')
                if rowskip > 0:
                    print(f'{rowskip} rows were skipped were skipped due to incorrect formatting.') #Allowing user to go back and fix file if a lot of items were skipped
                    end = input('To continue to calculate risk for correctly formatted rows, type "Y", to enter a different CSV, type "N": ')
                    if end.upper() == 'Y':
                        break
                else:
                    break
            else:
                print()
                print('File not found or not in format .csv, please input correct file name for .csv that exists within the same directory as this script.')
                print()

    with open('coords.csv', 'w', newline='') as file:   #Writing manual input coordinates to a .csv file if manual entry was chosen
        fwriter = csv.writer(file)
        fwriter.writerow(['x', 'y'])
        for iter in range(len(input_coordX)):
            fwriter.writerow([input_coordX[iter], input_coordY[iter]])


    print("Please weight the hazards. Allocate a percentage to each of the three hazards, totaling 100%")
    while True:                     #Getting a weighting factor for each of the hazards and allowing user to adjust if they do not meet requirements
        earthWeight= int(input("\tEarthquake Shaking Potential: "))
        fireWeight=  int(input("\tFire Hazard Severity Zone Rating: "))
        floodWeight= int(input("\tFlood Hazard: "))
        if earthWeight + fireWeight + floodWeight != 100:
            print("Weights entered do not add to 100, please enter different weights.")
        else:
            break



    # Set arcpy environment settings
    workspace = cwd + r"\group4_psp.gdb"

    # Set Local Variables
    coordinatesystem = arcpy.SpatialReference(3310)
    calipoly = 'CaliStatePoly'
    firepoly = 'CaliFireHazardSeverity'
    floodpoly = 'FloodData'
    quakepoly = 'EarthquakeRisk'
    #Set lists of risks to supply pointidentity function
    risks = [firepoly, quakepoly, floodpoly]
    #Set list of fields to return data for from pointidentity function
    outfields = ['FID_inpoint', 'Shape@XY', 'FID_CaliStatePoly', 'HAZ_CODE', 'SA10_2_', 'Reclass']

    pointrisks = pointidentity(cwd + r'\coords.csv', workspace, risks, outfields, coordinatesystem, locationfeat=calipoly)
    

    outlist = [] #Establish list to contain final calculated values for output
    for point in pointrisks:                                         # Make note of points not in California
        outval = []                                                 # Establish list to contain calculated data for each point
        outval.append(point[0])                                     # Append point FID
        outval.append(point[1])                                     # Append point coordinates
        if point[2] == -1:                                          # Check if point was in California, append message if not.
            outval.append('')
            outval.append('')
            outval.append('')
            outval.append('Not in California')
        else:                                                       # Standardize criteria values for each risk:
            # Identity returns areas where there is no data as '0', which are kept as 0 with the following formulas
            outval.append(round((float(point[3]) / 3) * 10))        # Converts fire risk value to value out of 10
            outval.append(round((float(point[4]) / 2.15) * 10))     # Converts earthquake risk value to value out of 10
            if point[5] == 2:                                       # Returns 10 if point within flood plain, returns 1 if not.
                outval.append(10)
            elif point[5] == 1:
                outval.append(1)                                    
            else:
                outval.append(0)                                    # Returns 0 if no data
        outlist.append(outval)
        
    for val in outlist:
        if len(val) < 6:
            val.append(round(indexcalc(val[2:], [earthWeight, fireWeight, floodWeight])))

    print(outlist) #For debugging


    print('************************************************************************************************') 
    print()
    print("California Home Natural Disaster Danger Index:")
    for item in outlist:
        if item[5] == 'Not in California':
            print(f'The location {str(item[1])} is not in california')
        else:
            print("At the location " + str(item[1]) + ":")
            print("\tThe Earthquake Shaking Potential is:          " + str(item[2]) + " /10")
            print("\tThe Fire Hazard Severity Zone Rating is:      " + str(item[3]) + " /10")
            print("\tFlood Plain Presence:                         " + str(item[4]))
            print("\tThe Danger Index is:                          " + str(item[5]) + " /10")
            print()

    with open('CaliDangerIndex.txt', 'w') as file:
        file.write(f": {'FeatureID':10} : {'X':20} : {'Y':20} : {'Fire Risk':20} : {'Earthquake Risk':20} : {'Flood risk':20} : {'Danger Index':20} :\n")
        for item in outlist:
            file.write(f": {item[0]:10} : {round(item[1][0]):20} : {round(item[1][1]):20} : {item[2]:20} : {item[3]:20} : {item[4]:20} : {item[5]:20} :\n")

if __name__ == '__main__':
    main()
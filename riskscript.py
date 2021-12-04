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
    print("Use this program to calculate a Danger Index for Earthquake, Fire and Flood risk at your location(s) in California")
    print()
    print('************************************************************************************************') 
    print()

    # Kacy - Data Input
    print("Please choose method of input: manual entry or by input file.")
    inputSelection= str(input("\tEnter 'M' for manual or 'F' for file: "))

    input_coordX = []        	
    input_coordY = []    

    if inputSelection.upper() == "M":
            

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
            # determine whether user wants to enter another set of input values
            end = str(input("Do you want to stop entering values (Y/N)? "))
            print()
            if  end.upper() == 'Y':
                break

    else:
        while True:
            print()
            print('CSV should have header row, X coordinates in first column, Y coordinates in second column.')
            in_table = cwd + '/' + input('Please enter your coordinate CSV filename without extension: ') + ".csv"
            if os.path.isfile(in_table): #Checks if file really exists and is CSV.
                with open(in_table) as filein:
                    inreader = csv.reader(filein)
                    next(inreader)
                    rowskip = 0
                    for row in inreader:
                        coordX_sani = row[0].replace('.','').replace('-','')
                        coordY_sani = row[1].replace('.','').replace('-','')
                        if (not coordX_sani.isdecimal()) or (not coordY_sani.isdecimal()):
                            rowskip += 1
                        else:
                            input_coordX.append(row[0])
                            input_coordY.append(row[1])
                print('File successfully read.')
                if rowskip > 0:
                    print(f'{rowskip} rows were skipped were skipped due to incorrect formatting.')
                    end = input('To continue to calculate risk for correctly formatted rows, type "Y", to enter a different CSV, type "N".')
                    if end.upper() == 'Y':
                        break
                else:
                    break
            else:
                print()
                print('File not found or not in format .csv, please input correct file name for .csv that exists within the same directory as this script.')
                print()

    with open('coords.csv', 'w', newline='') as file:
        fwriter = csv.writer(file)
        fwriter.writerow(['x', 'y'])
        for iter in range(len(input_coordX)):
            fwriter.writerow([input_coordX[iter], input_coordY[iter]])


    print("Please weight the hazards. Allocate a percentage to each of the three hazards, totaling 100%")
    while True:
        earthWeight= int(input("\tEarthquake Shaking Potential: "))
        fireWeight=  int(input("\tFire Hazard Severity Zone Rating: "))
        floodWeight= int(input("\tFlood Hazard: "))
        if earthWeight + fireWeight + floodWeight != 100:
            print("Weights entered do not add to 100, please enter different weights.")
        else:
            break



    # Set arcpy environment settings
    arcpy.env.workspace = cwd + r"\group4_psp.gdb"
    arcpy.env.overwriteOutput = True

    print(arcpy.ListFeatureClasses())

    # Set Local Variables
    # Set the local variables
    x_coords = "x"
    y_coords = "y"

    point_feat = "testpoint"
    out_feat = "pointrisks"

    calipoly = 'CaliStatePoly'
    firepoly = 'CaliFireHazardSeverity'
    floodpoly = 'FloodData'
    quakepoly = 'EarthquakeRisk'

    arcpy.management.XYTableToPoint(in_table, point_feat, x_coords, y_coords) # Create XY Event Layer

    risks = [firepoly, quakepoly, floodpoly] # List of risks under consideration

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

    outlist = [] #Establish list to contain final calculated values for output
    for point in outpoints:                                         # Make note of points not in California
        outval = []                                                 # Establish list to contain calculated data for each point
        outval.append(point[0])                                     # Append point FID
        outval.append(point[1])                                     # Append point coordinates
        if point[2] == -1:                                          # Check if point was in California, append message if not.
            outval.append('Not in California')
        else:                                                       # Standardize criteria values for each risk:
            # Identity returns areas where there is no data as '0', which are kept as 0 with the following formulas
            outval.append(round((float(point[3]) / 3) * 10))        # Converts fire risk value to value out of 10
            outval.append(round((float(point[4]) / 2.15) * 10))     # Converts earthquake risk value to value out of 10
            outval.append(-1)
            if point[5] == 2:                                       # Returns 10 if point within flood plain, returns 1 if not.
                outval.append(10)
            elif point[5] == 1:
                outval.append(1)                                    
            else:
                outval.append(0)                                    # Returns 0 if no data
        outlist.append(outval)

        
    for val in outlist:
        if val[2] != 'Not in California':
            val.append(indexcalc(val[2:], [earthWeight, fireWeight, floodWeight]))


    # Delete output feature layer when data is extracted - UNCOMMMENT WHEN BUILD COMPLETE
    arcpy.management.Delete(out_feat)

    # print(outpoints)

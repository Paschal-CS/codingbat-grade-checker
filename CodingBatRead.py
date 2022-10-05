import csv
import glob
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

################################################################################
# items the end user should edit!-----------------------------------------------
################################################################################

# Login Credentials
# See next variable for credentials file option.
username = 'username'
password = 'password'

# Should the program read the credentials from codingbat_auth.txt
# instead of using the above values?
# The file should consist of two lines:
#   username on first line
#   password on second line
READCREDS = True

# Should the program print the names of students who haven't
# finished any problems since the last grade pull?
PRINTNONE = False

# TO DO
# Should the program save a copy of the report in a text file?
# doReport = True

# Should the program fetch results of custom problems?
# These will be stored in a separate group of CSV files
PROCESSCUSTOM = True

################################################################################
# helper functions   -----------------------------------------------------------
################################################################################

# getStudents function.  Reads a given csv file and returns a 2D list of the file's data.
def getStudents( fileName ) :
    students = []
    with open(fileName, newline='', encoding='utf-8') as myfile:
        reader = csv.reader(myfile)
        for row in reader :
            temp = row[0]
            row[0] = row[1]
            row[1] = temp
            students.append(row)
    return students

# writereport function. Given a CSV filename and the BeautifulSoup for a CodingBat page,
# writes out the webpage data into the CSV file.
def writereport( soupy, myfile ) :
    with open( myfile, 'w', newline='', encoding='utf-8') as file:

        writer = csv.writer(file)

        # Section names - write them to the first line of the csv file.
        # The first two and the last are manual names.
        sections = []
        sections.append('User ID')
        sections.append('Memo')
        sectionkeys = soupy.find_all(attrs={"name": "sectionkey"})
        for key in sectionkeys :
            sections.append(key.attrs.get('value'))
        sections.append('Total')
        writer.writerow(sections)

        # Find the Score data in the CodingBat structure.
        # Starts with the 6th <tr> tag.
        trs = soupy.find_all('tr')
        for tableTR in trs[5:] :
            # Build the data for this student. All data in separate <td> tags.
            # The first two tags are text.
            # The rest of the tags are numeric (replace blank with zero)
            student = []
            tds = tableTR.find_all('td')
            for j, tableTD in enumerate(tds) :
                if j <= 1 :
                    student.append( str(tableTD.text) )
                else :
                    student.append( int( float( str(tableTD.text).strip() or 0) ) )
            # Write this student to a line of csv
            writer.writerow(student)

def filechanges( filelist ) :
    # Get the most recent two csv files and extract their data.
    fileold = getStudents( filelist[1] )
    filenew = getStudents( filelist[0] )

    print( "Generating changes since \"" + filelist[1] + "\"\n")

    # This is O(n^2), but in any reasonable scenario a teacher with
    # CodingBat students has few enough students
    # that this process takes << 1 second on even modest hardware.
    for student in sorted( filenew[1:] ) :
        for student2 in sorted( fileold[1:] ) :
            if student[1] == student2[1] :
                # Matching student record from past and present found.
                # Loop through all sections. Print info if more problems have been completed.
                printed = False
                studentID = student[0] + " <" + student[1] + ">"
                # starting at index 2 because the first two are name and email.
                for i in range( 2, len( student ) ) :
                    printedThis = False
                    matchMe = filenew[0][i]
                    newVal = int(student[i])
                    for j in range( 2, len( student2 ) ) :
                        if matchMe == fileold[0][j] :
                            oldVal = int(student2[j])
                            if newVal > oldVal :
                                print( studentID + " has done " + str(newVal - oldVal) + " more problems in section " + filenew[0][i] + " -- total = " + str(newVal) )
                                printed = True
                                printedThis = True
                            elif newVal == oldVal :
                                printedThis = True
                    if printedThis is False and newVal > 0 :
                        print( studentID + " has done " + str(newVal) + " more problems in section " + filenew[0][i] + " -- total = " + str(newVal) )
                        printed = True
                if printed :
                    print()
                elif PRINTNONE :
                    print( studentID + " hasn't done any problems since the last score pull.\n")
                break

def processArchive( findstring, myfile ) :
    # Get the list of all codingbat csv files, sort by newest.
    filelist = glob.glob( findstring )
    filelist.sort(reverse=True)

    # Terminate if only one csv file has been created yet.
    if len(filelist) > 1 :
        filechanges(filelist)
    else :
        print("First set of CodingBat scores have been read and stored in " + myfile + ".")

################################################################################
# items the user shouldn't edit ------------------------------------------------
################################################################################

# Codingbat post fields
userfield = 'uname'
passwdfield = 'pw'

# Codingbat urls
login_url = 'https://codingbat.com/login'
fetch_url = 'https://codingbat.com/report'
custom_fetch_url = 'https://codingbat.com/report?java=on&custom=on&homepath=&form='

#today's date
today = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")

# filename prefix and suffix
prefix = 'codingbat_scores_'
suffix = '.csv'

# filename
csvfile = prefix + today + suffix
custom_csvfile = 'custom_' + csvfile

# report filename
reportfile = prefix + 'report_' + today + '.txt'
custom_reportfile = prefix + 'report_' + today + '_custom.txt'

# filename search string for glob
searchstring = os.getcwd() + os.path.sep + prefix + '*' + suffix
custom_searchstring = os.getcwd() + os.path.sep + 'custom_' + prefix + '*' + suffix

# read credentials, if needed
if READCREDS :
    credsfile = open("codingbat_auth.txt", "r", encoding='utf-8')
    username = credsfile.readline().strip()
    password = credsfile.readline().strip()
    credsfile.close()

################################################################################
# the actual program -----------------------------------------------------------
################################################################################

# make session
session = requests.Session()

# Credentials
credentials = {userfield:username, passwdfield:password}

# Post credentials
session.post(login_url, data=credentials)

# Load the CodingBat report page.
reportpage = session.get(fetch_url)

# Parse the report page with BeautifulSoup
soup = BeautifulSoup(reportpage.text, 'html.parser')

# Write the report to a csv file
writereport( soup, csvfile )

# Find the relevant CSV files and process!
processArchive(searchstring, csvfile)

# Last four steps for Custom Page if needed.
if PROCESSCUSTOM :
    customreportpage = session.get(custom_fetch_url)
    customsoup = BeautifulSoup(customreportpage.text, 'html.parser')
    writereport( customsoup, custom_csvfile )
    processArchive(custom_searchstring, custom_csvfile)

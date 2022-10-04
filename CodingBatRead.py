import csv
import glob
import os
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

'''
This program was written for Python 3

MIT License

Copyright (c) 2020 Thomas Kiesel <thomas.j.kiesel@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

################################################################################
# items the end user should edit!-----------------------------------------------
################################################################################

# Login Credentials
username = 'username'
password = 'password'

# Should the program print the names of students who haven't
# finished any problems since the last grade pull?
printNone = True

# Should the program read the credentials from codingbat_auth.txt
# instead of using the above values?
# The file should consist of two lines:
#   username on first line
#   password on second line
readCreds = True

# Should the program save a copy of the report in a text file?
doReport = True

################################################################################
# helper functions   -----------------------------------------------------------
################################################################################

# getStudents function.  Reads a given csv file and returns a 2D list of the file's data.
def getStudents( fileName ) :
    students = []
    with open(fileName, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader :
            temp = row[0]
            row[0] = row[1]
            row[1] = temp
            students.append(row)
    return students

################################################################################
# the actual program -----------------------------------------------------------
################################################################################

# Codingbat post fields
userfield = 'uname'
passwdfield = 'pw'

# Codingbat urls
login_url = 'https://codingbat.com/login'
fetch_url = 'https://codingbat.com/report'

#today's date
today = date.today().strftime("%Y-%m-%d")

# filename prefix and suffix
prefix = 'codingbat_scores_'
suffix = '.csv'

# filename
csvfile = prefix + today + suffix

# report filename
reportfile = prefix + 'report_' + today + '.txt'

# filename search string for glob
searchstring = os.getcwd() + os.path.sep + prefix + '*' + suffix

# read credentials, if needed
if readCreds :
    credsfile = open("codingbat_auth.txt", "r")
    username = credsfile.readline().strip()
    password = credsfile.readline().strip()
    credsfile.close()

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
with open( csvfile, 'w', newline='') as file:

    writer = csv.writer(file)

    # Section names - write them to the first line of the csv file.
    # The first two and the last are manual names.
    sections = []
    sections.append('User ID')
    sections.append('Memo')
    sectionkeys = soup.find_all(attrs={"name": "sectionkey"})
    for key in sectionkeys :
        sections.append(key.attrs.get('value'))
    sections.append('Total')
    writer.writerow(sections)

    # Find the Score data in the CodingBat structure.  
    # Starts with the 6th <tr> tag.
    trs = soup.find_all('tr')
    for i, tableTR in enumerate(trs) :
        if i >= 5 :
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
        

# Get the list of all codingbat csv files, sort by newest.
filelist = glob.glob( searchstring )
filelist.sort(reverse=True)

# Terminate if only one csv file has been created yet.
if len(filelist) < 2 :
    print("First set of CodingBat scores have been read and stored in " + csvfile + " ... Exiting.")
    sys.exit()

# Get the most recent two csv files and extract their data.
fileold = getStudents( filelist[1] )
filenew = getStudents( filelist[0] )

print( "Generating changes since \"" + filelist[1] + "\"\n")

# This is O(n^2), but in any reasonable scenario a teacher with CodingBat students has few enough students
# that this process takes << 1 second on even modest hardware.
for student in sorted( filenew[1:] ) :
    for student2 in sorted( fileold[1:] ) :
        if student[1] == student2[1] :
            # Matching student record from past and present found. 
            # Loop through all sections. Print info if more problems have been completed.
            printed = False
            studentID = student[0] + " <" + student[1] + ">"
            for i in range( len( student ) ) :
                if i > 1 :
                    printedThis = False
                    matchMe = filenew[0][i]
                    newVal = int(student[i])
                    for j in range( len( student2 ) ) :
                        if matchMe == fileold[0][j] :
                            oldVal = int(student2[j])
                            if newVal > oldVal :
                                print( studentID + " has done " + str(newVal - oldVal) + " more problems in section " + filenew[0][i] + " -- total = " + str(newVal) )
                                printed = True
                                printedThis = True
                            elif newVal == oldVal :
                                printedThis = True                            
                    if printedThis == False and newVal > 0 :
                        print( studentID + " has done " + str(newVal) + " more problems in section " + filenew[0][i] + " -- total = " + str(newVal) )
                        printed = True
            if printed :
                print()
            elif printNone :
                print( studentID + " hasn't done any problems since the last score pull.\n")
            break
            
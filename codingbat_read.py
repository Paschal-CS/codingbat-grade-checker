"""A program that automatically fetches student data from CodingBat

The program will also compare the most recent data pull to the most recent
previous one (if one exists) and give reporting about student progress
in the interim
"""
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
USERNAME = 'username'
PASSWORD = 'password'

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

def get_students( file_name ) :
    """Reads a given csv file and returns a 2D list of the file's data."""
    students = []
    with open(file_name, newline='', encoding='utf-8') as myfile:
        reader = csv.reader(myfile)
        for row in reader :
            temp = row[0]
            row[0] = row[1]
            row[1] = temp
            students.append(row)
    return students

def writereport( soupy, myfile ) :
    """Given the bs of a page and a CSV filename, writes the webpage data into the CSV file."""
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
        for table_tr in trs[5:] :
            # Build the data for this student. All data in separate <td> tags.
            # The first two tags are text.
            # The rest of the tags are numeric (replace blank with zero)
            student = []
            tds = table_tr.find_all('td')
            for j, table_td in enumerate(tds) :
                if j <= 1 :
                    student.append( str(table_td.text) )
                else :
                    student.append( int( float( str(table_td.text).strip() or 0) ) )
            # Write this student to a line of csv
            writer.writerow(student)

def file_changes( filelist ) :
    """Given a sorted list of CSV student data files, examine changes between them."""
    # Get the most recent two csv files and extract their data.
    fileold = get_students( filelist[1] )
    filenew = get_students( filelist[0] )

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
                student_id = student[0] + " <" + student[1] + ">"
                # starting at index 2 because the first two are name and email.
                for i in range( 2, len( student ) ) :
                    printed_this = False
                    match_me = filenew[0][i]
                    new_val = int(student[i])
                    for j in range( 2, len( student2 ) ) :
                        if match_me == fileold[0][j] :
                            old_val = int(student2[j])
                            if new_val > old_val :
                                print_report(student_id, new_val, old_val, filenew[0][i])
                                printed = True
                                printed_this = True
                            elif new_val == old_val :
                                printed_this = True
                    if printed_this is False and new_val > 0 :
                        print_report(student_id, new_val, 0, filenew[0][i])
                        printed = True
                if printed :
                    print()
                elif PRINTNONE :
                    print( student_id + " hasn't done any problems since the last score pull.\n")
                break

def print_report( sid, new_val, old_val, section ) :
    """print student progress line"""
    report = sid + " has done " + str(new_val - old_val) \
        + " more problems in section " + section \
        + " -- total = " + str(new_val)
    print( report )

def process_archive( findstring, myfile ) :
    """Given a glob string and a filename, generate a list of files for file_changes() and report"""
    # Get the list of all codingbat csv files, sort by newest.
    filelist = glob.glob( findstring )
    filelist.sort(reverse=True)

    # Terminate if only one csv file has been created yet.
    if len(filelist) > 1 :
        file_changes(filelist)
    else :
        print("First set of CodingBat scores have been read and stored in " + myfile + ".")

################################################################################
# items the user shouldn't edit ------------------------------------------------
################################################################################

# Codingbat post fields
USERFIELD = 'uname'
PASSWDFIELD = 'pw'

# Codingbat urls
LOGIN_URL = 'https://codingbat.com/login'
FETCH_URL = 'https://codingbat.com/report'
CUSTOM_FETCH_URL = 'https://codingbat.com/report?java=on&custom=on&homepath=&form='

#today's date
today = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")

# filename prefix and suffix
PREFIX = 'codingbat_scores_'
SUFFIX = '.csv'

# filename
csvfile = PREFIX + today + SUFFIX
custom_csvfile = 'custom_' + csvfile

# report filename
reportfile = PREFIX + 'report_' + today + '.txt'
custom_reportfile = PREFIX + 'report_' + today + '_custom.txt'

# filename search string for glob
searchstring = os.getcwd() + os.path.sep + PREFIX + '*' + SUFFIX
custom_searchstring = os.getcwd() + os.path.sep + 'custom_' + PREFIX + '*' + SUFFIX

# read credentials, if needed
if READCREDS :
    credsfile = open("codingbat_auth.txt", "r", encoding='utf-8')
    USERNAME = credsfile.readline().strip()
    PASSWORD = credsfile.readline().strip()
    credsfile.close()

################################################################################
# the actual program -----------------------------------------------------------
################################################################################

# make session
session = requests.Session()

# Credentials
credentials = {USERFIELD:USERNAME, PASSWDFIELD:PASSWORD}

# Post credentials
session.post(LOGIN_URL, data=credentials)

# Load the CodingBat report page.
report_page = session.get(FETCH_URL)

# Parse the report page with BeautifulSoup
soup = BeautifulSoup(report_page.text, 'html.parser')

# Write the report to a csv file
writereport( soup, csvfile )

# Find the relevant CSV files and process!
process_archive(searchstring, csvfile)

# Last four steps for Custom Page if needed.
if PROCESSCUSTOM :
    custom_report_page = session.get(CUSTOM_FETCH_URL)
    customsoup = BeautifulSoup(custom_report_page.text, 'html.parser')
    writereport( customsoup, custom_csvfile )
    process_archive(custom_searchstring, custom_csvfile)

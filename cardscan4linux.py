#!/usr/bin/env python

# Version: 1.1.0
# Author: Adam Govier (ins1gn1a) - September 2015
# Email: me@ins1gn1a.com
#
# Disclaimer:
# I am not responsible for any problems or issues that are potentially caused 
# by running this tool. There should not be any problems as this script uses
# in-built functionality and was created with performance and availability 
# in mind. Nevertheless, you've been told!

# Modules
import timeit
import re
import os
import sys
import argparse
import subprocess
from itertools import islice

# Colouring!
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Input argument setup
p = argparse.ArgumentParser(description='Search Linux-based systems for payment card numbers (VISA, AMEX, Mastercard).')
p.add_argument('-o','--output',dest='output',help='Output data to a file instead of the Terminal.',action='store_true')
p.add_argument('-D','--max-depth',dest='depth',help='Enter the max depth that the scanner will search from the given directory (Default is 3).',type=int,default=3)
p.add_argument('-d','--min-depth',dest='mindepth',help='Enter the min depth that the scanner will search from the given directory (No Default).',type=int)
p.add_argument('-l','--lines',dest='lines',help='Enter the number of lines from the file to cycle through (Default is 50)',type=int,default=50)
p.add_argument('-p','--path',help='Input the directory path that you want to recursively search through, e.g. /var (Default is /)',default='/')
p.add_argument('-e','--extensions',dest='extensions',help='Input the file extensions that should be searched for, separated by spaces.',required=True,nargs='+')
p.add_argument('-x','--exclude',dest='exclude_dir',help='Input the directories to exclude, separated by spaces. Wildcards can be used, e.g. /var/*',required=False,nargs='+',default="")
p.add_argument('-max','--max-size',help='Enter the maximum file-size to search for (Default 100 Kilobytes). Units: "c" for bytes, "k" for Kilobytes, "M" for Megabytes',dest="maxsize",default="100k")
p.add_argument('-min','--min-size',help='Enter the minimum file-size to search for (Default 16 Bytes). Units: "c" for bytes, "k" for Kilobytes, "M" for Megabytes',dest="minsize",default="16c")
p.add_argument('-mount','--scan-mount',dest='mounted',help='Enable to scan the mounted remote file systems (Default is off.)',required=False,action='store_true')
p.add_argument('-v','--verbose',dest='verbose',help='Display verbose messages (Warning: output can be huge).',required=False,action='store_true')
a = p.parse_args()

# Banner
print "----------------------------------------------------------------------------"
print "  ____              _ ____                  _  _   _     _           "
print " / ___|__ _ _ __ __| / ___|  ___ __ _ _ __ | || | | |   (_)_ __  _   ___  __"
print "| |   / _` | '__/ _` \___ \ / __/ _` | '_ \| || |_| |   | | '_ \| | | \ \/ /"
print "| |__| (_| | | | (_| |___) | (_| (_| | | | |__   _| |___| | | | | |_| |>  <"
print " \____\__,_|_|  \__,_|____/ \___\__,_|_| |_|  |_| |_____|_|_| |_|\__,_/_/\_\ "
print "----------------------------------------------------------- Version 1.1.0 --"

# String concatenation for file extension searching.
extCmd = ""
z = 0
for ext in a.extensions:
        if z == 0:
                extCmd = " -name '*.%s'" %(ext)
                z += 1
        else:
                extCmd = extCmd + (" -o -name '*.%s'" %(ext))
                z += 1

# Sizing
max = ("-size -" + a.maxsize) # Default 100 Kilobytes (100k)
min = ("-size +" + a.minsize) # Default 16 bytes (16 c)

# Exclude files via -x/--exclude
y = 0
exclude_cmd = ""
for excl in a.exclude_dir:
        if y == 0:
                exclude_cmd = " ! -path '%s/*'" %(excl)
                y += 1
        else:
                exclude_cmd = exclude_cmd + (" -a ! -path '%s/*'" %(excl))
                y += 1
				
if y > 0:
	exclude_cmd = exclude_cmd + " "
	header_exclusions = a.exclude_dir
else:
	header_exclusions = "None"

# Output to stdout
if len(a.extensions) > 3:
	header_line = "=============================================================================="
else:
	header_line = "========================================================="
print (bcolors.HEADER + header_line)
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Root Path \t\t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(a.path))
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Max Size \t\t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(a.maxsize))
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Min Size \t\t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(a.minsize))
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Extensions \t\t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(a.extensions))
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Lines per file \t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(a.lines))
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Depth of search \t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(a.depth))
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Scan Mounted Dirs \t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(a.mounted))
print (bcolors.HEADER + "[*]" + bcolors.ENDC + " Exclusions \t\t" + bcolors.HEADER + ":\t" + bcolors.ENDC + str(header_exclusions))
print (bcolors.HEADER + header_line + bcolors.ENDC)
print (bcolors.OKGREEN + "\n[*] " + bcolors.ENDC + "Starting file-system scan. This may take a while...")
start_time = timeit.default_timer()

# Local or Remote Mounting
if a.mounted:
    remote_mount = ""
else:
    remote_mount = "-mount "

# Min depth
if a.mindepth is None:
    min_depth = ""
else:
    min_depth = "-mindepth %s " %(str(a.mindepth))
	
# Create a list of all files with the provided inputs
try:
        full_path_list = subprocess.check_output('find %s %s-maxdepth %s %s-type f \( %s %s\) %s %s ' %(a.path,remote_mount,a.depth,min_depth,extCmd,exclude_cmd,max,min), shell=True)
        full_path_list = full_path_list.rstrip().split('\n')
except:
        sys.exit(bcolors.FAIL + "[*] " + bcolors.ENDC + "Cannot retrieve file list - Likely too many symbolic links.")

# Count how many entries in the list file
file_lines = len(full_path_list)

# Output to user
print (bcolors.OKGREEN + "[*] " + bcolors.ENDC + "File-system search complete. " + str(file_lines) + " files to check for card-data.")

# Regex to filter card numbers
regexAmex = re.compile("([^0-9-]|^)(3(4[0-9]{2}|7[0-9]{2})( |-|)[0-9]{6}( |-|)[0-9]{5})([^0-9-]|$)") #16 Digit AMEX
regexVisa = re.compile("([^0-9-]|^)(4[0-9]{3}( |-|)([0-9]{4})( |-|)([0-9]{4})( |-|)([0-9]{4}))([^0-9-]|$)")
regexMaster = re.compile("([^0-9-]|^)(5[0-9]{3}( |-|)([0-9]{4})( |-|)([0-9]{4})( |-|)([0-9]{4}))([^0-9-]|$)")

# Log file - counting
total_count = 0

# Search through files in the list
try:
        for filepath in full_path_list:
                filepath = filepath.rstrip('\n')
                try:
                        with open(filepath) as file:
                                if a.verbose:
                                        print filepath
                                total_count += 1
                                with open('/tmp/cardscan4linux.log', 'w') as log_file:
                                        log_file.write(str(file_lines) + "/" + str(total_count) + "\n")

                                i = 0
                                results = []
                                head = list(islice(file, a.lines)) # Opens 50 lines by default

                                # Loops through each item in list
                                for item in head:
                                        amex = re.search(regexAmex, item.rstrip('\n'))
                                        visa = re.search(regexVisa, item.rstrip('\n'))
                                        master = re.search(regexMaster, item.rstrip('\n'))

                                        # Prints if matches AMEX
                                        if amex:
                                                i += 1
                                                results.append("\tAMEX:\t\t " + bcolors.FAIL + amex.group().replace(',','').strip() + bcolors.ENDC)

                                        # Prints if matches VISA
                                        elif visa:
                                                i += 1
                                                results.append("\tVISA:\t\t "  + bcolors.FAIL + visa.group().replace(',','').strip() + bcolors.ENDC)

                                        # Prints if matches Mastercard
                                        elif master:
                                                i += 1
                                                results.append("\tMASTERCARD:\t " + bcolors.FAIL + master.group().replace(',','').strip() + bcolors.ENDC)

                                if i > 0:
                                        if a.output:
                                                with open('cardscan.output', "a") as outfile:
                                                        outfile.write("File: " + filepath + "\n")
                                                        for result in results:
                                                                outfile.write(result + "\n")
                                        else:
                                                print ("\nFile: " + filepath)
                                                for result in results:
                                                        print result

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    with open('cardscan4linux-error.log','a') as errlog:
                        errlog.write("File: " + filepath + "\n" + e + "\n")
                        sys.exit(bcolors.FAIL + "[*] " + bcolors.ENDC + "Cannot open file '" + filepath + "'.")
except:
        sys.exit(bcolors.WARNING + "\r[*] " + bcolors.ENDC + "There are no files that match the search.")

# Removes the temp file
try:
        os.remove("/tmp/cardscan4linux.log")
except OSError:
        pass

total_time = int(timeit.default_timer()) - int(start_time)
# End of file
print (bcolors.OKGREEN + "[*] " + bcolors.ENDC + "Card scanning complete. " + str(file_lines) + " total files were scanned in " + str(total_time) + " seconds.")
if a.output:
        print (bcolors.OKGREEN + "[*] " + bcolors.ENDC + "Output saved to " + (os.path.dirname(os.path.realpath(__file__))) + "/cardscan.output.")

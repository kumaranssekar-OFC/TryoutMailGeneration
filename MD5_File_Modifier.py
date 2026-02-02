'''
Author: Kumaran Sekar (EUJ1COB)
Created : 25-09-2023

Features:
25-09-2023            1. Remove the _content.md5 file
22-11-2023            2. Rename the _content.md5.verify to _content.md5
22-11-2023            3. Added a another condition to check if only the verify file is there and rename
22-11-2023            4. Cmd line parser is adapted to get the input.
29-11-2023            5. New function is created to call the "chk_md5.pl" script and added time and date, when it starts and when its completed.
'''
from logging import exception
from math import e
import os
from pathlib import Path
import subprocess
import sys
import optparse
import win32api
import time
import datetime
from datetime import datetime
from os.path import exists
class Remove_Rename_file:

    def __init__(self, Myfile):
        self.Myfile = Myfile
        self.cont = "_content.md5"
        self.contVer = "_content.md5.verify"
        
    def call_check_md5(self):
        perl_script = "chk_md5.pl"
        StartTime = datetime.now()
        print ("Execution Starts at :", str(StartTime))
        var = str(self.Myfile)
        file_exists = exists(perl_script)

        if (file_exists == True):
            pipe = subprocess.call(["perl", perl_script , var])
        else: 
            RED = '\033[91m'
            END = '\033[0m'
            BOLD = '\033[1m'
            print (RED + BOLD  +  f"The check sum is not calculated. Since, the {perl_script} file is not exists. " + END)
    
    def removeFile_MainDirectory(self):
        GREEN =  '\033[32m' 
        END = '\033[0m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        ContentFile = os.path.join(self.Myfile, self.cont)
        ContentFileVerify = os.path.join(self.Myfile, self.contVer)
        self.list_dir = os.listdir(self.Myfile)
        try:
            if os.path.isfile(ContentFile) and os.path.isfile(ContentFileVerify):
                os.remove(ContentFile)
                print (GREEN + f"{self.cont} is successfully removed"+ END)
                os.rename(ContentFileVerify, ContentFile)
                print (GREEN + BOLD + f"{self.contVer} is successfully renamed to {self.cont}" + END)
            elif os.path.isfile(ContentFile) == False and os.path.isfile(ContentFileVerify) == True:
                os.rename(ContentFileVerify, ContentFile)
                print (GREEN + BOLD +  f"{self.contVer} is successfully renamed to {self.cont}" + END)            
            else:
                print (RED + BOLD + f"Either {self.contVer} or {self.cont} file is not available to delete or rename in {self.Myfile}" + END)
            
        except FileNotFoundError:
            print ("Parent Directory".center(40, "#"))

            print (f"{self.contVer} and {self.cont} is not available"
                    "\nIt might be already renamed and removed")

    def removeFile_Subdirectory (self):
        GREEN =  '\033[32m' 
        END = '\033[0m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        try:
            for i in self.list_dir:
                append_dir = os.path.join(self.Myfile, i)
                append_dir = str(append_dir) 
                if (os.path.isdir(append_dir)):
                    ContentFile = os.path.join(append_dir, self.cont)
                    ContentFileVerify = os.path.join(append_dir, self.contVer)
                    if os.path.isfile(ContentFile) and os.path.isfile(ContentFileVerify):
                        os.remove(ContentFile)
                        print (GREEN + f"{self.cont} is successfully removed" + END)
                        os.rename(ContentFileVerify, ContentFile)
                        print (GREEN + BOLD + f"{self.contVer} is successfully renamed to {self.cont}" + END) 
                    elif os.path.isfile(ContentFile) == False and os.path.isfile(ContentFileVerify) == True:
                        os.rename(ContentFileVerify, ContentFile)
                        print (GREEN + BOLD + f"{self.contVer} is successfully renamed to {self.cont}" + END)  
                    else:
                        print (RED + BOLD + f"Either {self.contVer} or {self.cont} file is not available to delete or rename in {append_dir}" + END)

        except:
            print ("Sub Directory".center(40, "#"))

            print (f"{self.contVer} and {self.cont} is not available"
                     "\nIt might be already renamed and removed ")

if __name__ == "__main__":

    parser = optparse.OptionParser()
    parser.add_option('-x', '--production path', dest='SW_Path', default=None,
                      help='Provide the SW Path for the input to check the content')
    (options, args) = parser.parse_args()
    
    if not options.SW_Path:
        SW_Path = str(input("\nPlease provide the SW Path:\n"))
    else:
        SW_Path = options.SW_Path
    
    obj1 = Remove_Rename_file(SW_Path)
    obj1.call_check_md5()
    obj1.removeFile_MainDirectory()
    obj1.removeFile_Subdirectory()
    endTime = datetime.now()
    print ("Execution Ends at ",endTime)
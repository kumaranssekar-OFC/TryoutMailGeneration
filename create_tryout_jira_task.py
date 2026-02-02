# -*- coding: utf-8 -*-
"""
Crafting started on 02-05-2024 @ 13:24 

By Creator: Kumaran Sekar (MS\ECR4-XC); (EUJ1COB);

Changes:
27-11-2024  :   Bug Fixes for the reuse part number is adding in the jira even for the actual part number.
31-10-2025  :   Bug Fixes.
31-10-2025  :   Successor and Predecessor part number organized based on thee Release type. Also additional update for updating the jira description
31-10-2025  :   Path Line Breaks are fixed. 
13-11-2025  :   Given Space in between SW in part number section at description.
13-11-2025  :   If the release is Device Conversion, the Stick update will update as "{Please Update manually}".
14-11-2025  :   Jira Updation with Correct part numbers.

"""

import code
from ctypes import LittleEndianStructure
from email.mime import base, image
import math
from opcode import opname
from operator import indexOf
from pdb import find_function
import re
from sqlite3 import Date
from traceback import print_tb
from unittest import skip
from jira import JIRA
from importlib.resources import path
import os
import glob
import pandas as pd
from JiraAccess import jira_access
import warnings
import subprocess
import ServerPath_File as SPF
import logging as log
from logging import handlers
import datetime

warnings.simplefilter(action='ignore', category=UserWarning)

__version = "01.00"

os.system('color')


NeedToRun = SPF.PathFormation.NeedToRun #Calling the ServerPath script to get the input from user for Sister device and Copy binaries confirmation.

#This is used to create and rotate the log file.
handlers.TimedRotatingFileHandler(filename="create_jira.log", when='M', interval=1, backupCount=4, encoding=None, delay=False, utc=False, atTime=datetime.datetime.now(), errors=None)

log.basicConfig(filename="create_jira.log", level=log.INFO, format='%(asctime)s, %(message)s', datefmt = '%Y-%m-%d %H:%M:%S' , encoding="UTF-8" )



class Jira_issue_create:

    def readCSV_InputFile(self): #Reading the input file and returning the values.
        #dfInit = pd.read_csv("init.csv")
        self.dfInit = pd.read_excel("init.xlsx")
        log.info(self.dfInit)
        return self.dfInit

    def set_inputs(self): #Assigning the values which is returned from the input file.
        init_excel = self.dfInit
        PartNumbers = init_excel['Part_Numbers']
        PrePartnumbers = init_excel['Predecessor_PN']
        SWVersion = init_excel['SW_Version']
        ReleaseTask = init_excel['Jira_Main_Task ']
        TOSubTask = init_excel['Jira_TO_Task']
        Task_Name = init_excel['Task_Name']
        ReleaseType = init_excel['Release_Type']
        Collection_ID = init_excel['Docushare_CollectionID']
        Base_SW  = init_excel['Base_SW']
        FCID_Ver = init_excel['FCID_Version']
        TO_HW_List = init_excel['HW_List']

        #re assigning the above value to below constructor variable so that we can access outside the function.
        
        self.task_issue_id = ReleaseTask[0] #input("Provide the Task jira ID: \n")
        self.to_task_issue_id = TOSubTask[0]
        self.task_name = Task_Name[0] #input("Enter the task name: \n")
        self.task_type =  ReleaseType[0]#input("Task type (Reflash / Image) \n")
        #print ("The task type is ", type(self.task_type))
        self.task_sw   =  SWVersion[0] #input("Enter the SW \n")
        self.part_number = PartNumbers #input ("Enter the part numbers : \n").split(",")
        self.PrePartnumbers = PrePartnumbers
        #print ("The task type is ", type(self.part_number))
        self._no_of_partnumbers = len(self.part_number)
        self._no_of_Ppartnumbers = len(self.PrePartnumbers)
        self.Collection_ID = Collection_ID[0]
        self.baseSW = Base_SW
        self.FCID_Ver = FCID_Ver[0]
        self.TO_HW_List = TO_HW_List[0]

        #empty value
        self.stt = ""
        self.extracted_data1 = ""
        self.extracted_data2 = ""
        self.extracted_data3 = ""

        return self.task_name, self.task_type, self.task_sw, self.part_number, self._no_of_partnumbers, self.task_issue_id, self.extracted_data1, self.extracted_data2, self.extracted_data3, self.to_task_issue_id, self.Collection_ID, self.baseSW, self.PrePartnumbers, self._no_of_Ppartnumbers
    
    def extract_description(self):
        try:
            self.BoschJira = jira_access()
            extract_issue =self.BoschJira.issue(str(self.task_issue_id).strip())
            extract_description = extract_issue.fields.description
            file_obj = open ("jira_issue_extraction.txt", "w")
            file_obj.writelines(str(extract_description).replace("\n", ""))
            file_obj.close()
        except AttributeError:
            print ("ERROR:", "Please check the Tryout Task Jira ID:")
            log.error("ERROR:", "Please check the Tryout Task Jira ID:")
            exit()
        print (self.task_name, "\n")
        file1 = open("jira_extracted_inputs.txt", "w+")
        multiple_task_name = []
        task_indexes = []
        with open("jira_issue_extraction.txt", "r") as fp:
            _file = fp.readlines()
            _dev_index = 0
            while (_dev_index < len(_file)):
            #for row in _file:
                if(_file[_dev_index].find(self.task_name) != -1):

                    task_lowercase = _file[_dev_index].lower()
                    if ("re-flash" in task_lowercase):
                        task_lowercase = task_lowercase.replace("re-flash", "reflash")
                    elif ("reflash" in task_lowercase):
                        task_lowercase = task_lowercase
               
                    if (self.task_type == "SplUpd" and "reflash" in task_lowercase):
                        task_indexes.append(_dev_index)
                    elif(self.task_type == "Image" and "reflash" not in task_lowercase):
                        task_indexes.append(_dev_index)

                _dev_index+=1

            for task_index in task_indexes:
                for _incre in range(0, 4):
                    print(_file[task_index + _incre])
                    if (self.task_sw in _file[task_index + _incre]):
                        multiple_task_name.append(_file[task_index])
                    
        fp.close()
        print (multiple_task_name)
        print ("\n --- Task(s) taken from JIRA is listed below --- \n")
        for task_names in multiple_task_name:
            print ("\n", "\033[93m", multiple_task_name.index(task_names), "\033[00m" ," - ", "\033[92m", task_names.replace("h3. {color: #FF0080}","").replace("h3. {color:#FF0080}","").replace("{color}", ""),"\033[00m")
            log.info (f'\n {multiple_task_name.index(task_names)} - {task_names.replace("h3. {color: #FF0080}","").replace("{color}", "")}')


        
        if(len(multiple_task_name) == 1):
            
            # print (colored (f"\n The task listed is only one, hence it is automatically selected - {multiple_task_name[0].replace('h3. {color: #FF0080}','').replace('{color}', '')})", "green")) \033[94m \033[00m  \e[0;96m

            print (f" \n Only one task is listed, thus it is automatically picked - \033[94m {multiple_task_name[0].replace('h3. {color: #FF0080}','').replace('h3. {color:#FF0080}','').replace('{color}', '')}\033[00m")

            log.info (f"\n The task listed is only one, hence it is automatically selected {multiple_task_name[0]}  ")
            select_task = 0
        elif (len(multiple_task_name) == 0):
            print (f"\n Error: The task list is empty, Please check the Task name or Task ID in input file.")
            log.info (f"\n Error: The task list is empty, Please check the Task name or Task ID in input file.")
            exit()
        else:
            select_task = int(input("\n Please enter the index number of the above listed task. : \n"))


        with open("jira_issue_extraction.txt", "r") as fp:
            _file = fp.readlines() 
            try:           
                for row in _file:
                    if(row.find(multiple_task_name[select_task]) != -1):
                        # print("string exists")
                        # print ("line number: ", _file.index(row))
                        pattern_to_replace = "h3.*80}"

                        change_to_lowerCase = _file[_file.index(row)].lower()
                        change_jira_taskname = str(multiple_task_name[select_task]).lower()
                        change_jira_taskname = re.sub(pattern_to_replace, '', change_jira_taskname)
                        if ("re-flash" in change_to_lowerCase):
                            change_to_lowerCase = change_to_lowerCase.replace("re-flash", "reflash")
                            change_jira_taskname = change_jira_taskname.replace("re-flash", "reflash")
                        elif ("reflash" in change_to_lowerCase):
                            change_to_lowerCase = change_to_lowerCase

                        # print ("The changes: ", change_to_lowerCase)

                        if (self.task_type == "SplUpd"):
                            if ("reflash" in change_to_lowerCase):
                                pattern = r'reflash start.*}*'
                                output_string = re.sub(pattern, '', change_jira_taskname)
                                if(str(self.task_name).lower() == output_string.strip()):
                                    print ("\n Info: The Given Task Name matches with the expected.")
                                    log.info ("\n Info: The Given Task Name matches with the expected.")
                                else:
                                    print (f"\n \t Warning: The Given Task Name : \n '{str(self.task_name).lower()}' is not matches with the expected \n '{output_string.strip()}'. Please check the init inputs.")
                                    log.info (f"\n \t Warning: The Given Task Name : \n '{str(self.task_name).lower()}' is not matches with the expected \n '{output_string.strip()}'. Please check the init inputs.")
                                #task_type = "reflash"
                                reflash_check = True
                                break
                            else:
                                reflash_check = False

                        else:
                            if ("reflash"  not in change_to_lowerCase):
                                pattern = r'start.*}'
                                output_string = re.sub(pattern, '', change_jira_taskname)
                                if(str(self.task_name).lower() == output_string.strip()):
                                    print ("\n Info: The Given Task Name matches with the expected.")
                                else:
                                    print (f"\n \t Warning: The Given Task Name : \n '{str(self.task_name).lower()}' is not matches with the expected \n '{output_string.strip()}'. Please check the init inputs.")
                                reflash_check = True #self.task_name in _file[_file.index(row)] and ref_word not in _file[_file.index(row)]
                                # print (reflash_check)
                                break
                            else:
                                reflash_check = False
                        if (reflash_check ==  True):
                            break
            except UnboundLocalError:
                print("\n Oops!  That was no valid number.  Try again...")
                log.error("\n Oops!  That was no valid number.  Try again...")
                exit()

            if (reflash_check):
                dev_expected = "Devices"
                _dev_index = 1
                try:
                    while (_dev_index < len(_file)):
                        # print("Task swin jira:", _file[_file.index(row) + _dev_index])
                        if (self.task_sw in _file[_file.index(row) + _dev_index]):
                            sw_task = self.task_sw in _file[_file.index(row) + _dev_index]
                            # print (f"the value is found in this line {_file.index(row) + _dev_index}", _file[_file.index(row) + _dev_index])
                            while (_dev_index < len(_file)):
                                if (dev_expected in _file[_file.index(row) + _dev_index]):
                                    print (f"the expected {dev_expected}, is available in line ",_file.index(row) + _dev_index )
                                    skip_section = _file.index(row) + _dev_index + 1
                                    total_no_lines  = self._no_of_partnumbers
                                    _taskDetails_write =""
                                    if (self.task_type == "SplUpd"): 
                                        for i in range (total_no_lines):
                                            print(self.part_number[i])
                                            for j in range(total_no_lines*2):
                                                print(self.part_number[i])
                                                print(_file[skip_section + i].replace("\n", ""))
                                                if (self.PrePartnumbers[i] in _file[skip_section + j]):
                                                    print ("yes")
                                                    _taskDetails = _file[skip_section + j]
                                                    print ("The Task Details are as follow", _taskDetails)
                                                    _taskDetails_replaced = _taskDetails.replace("|", " ").replace("(/)", "").replace("(-)", "").replace("\n", "").replace("(x)", "").replace("(!)", "").replace("*", "")
                                                    print ("The Task Details are as follow", _taskDetails_replaced)
                                                    _taskDetails_write = _taskDetails_write + _taskDetails_replaced + "\n"
                                                    print("The Task for allow", _taskDetails_write)
                                                    break
                                    else:
                                        for i in range (total_no_lines):
                                            print(self.part_number[i])
                                            for j in range(total_no_lines*2):
                                                print(self.part_number[i])
                                                print(_file[skip_section + i].replace("\n", ""))
                                                if (self.part_number[i] in _file[skip_section + j]):
                                                    print ("yes")
                                                    _taskDetails = _file[skip_section + j]
                                                    print ("The Task Details are as follow", _taskDetails)
                                                    _taskDetails_replaced = _taskDetails.replace("|", " ").replace("(/)", "").replace("(-)", "").replace("\n", "").replace("(x)", "").replace("(!)", "").replace("*", "")
                                                    print ("The Task Details are as follow", _taskDetails_replaced)
                                                    _taskDetails_write = _taskDetails_write + _taskDetails_replaced + "\n"
                                                    print("The Task for allow", _taskDetails_write)
                                                    break

                                    break
                                _dev_index += 1

                            break
                    
                        _dev_index += 1 
                except:
                    print ("\n Error: The SW might be incorrect in given Task. Please check the Task")
                    log.error("\n Error: The SW might be incorrect in given Task. Please check the Task")
                    exit()
        file1.write(_taskDetails_write)
        file1.close()

        fp.close()
        file1 = open("jira_extracted_inputs.txt", "r")
        self._jiradescription = file1.read()
        file1.close()

    def read_tryoutMail(self):
        try:
            
            _sw = ""
            _sw1 = "" #SW ID and TAG will be stored here.
            tryout_mailfile = open(f"{self.task_sw}.txt", 'r')
            Readtext = tryout_mailfile.readlines()

            for readlines in Readtext:
                if ("SW-ID" in readlines):
                    SW_ID = Readtext.index(readlines) # To find the index of SW ID.
                    _sw1 += readlines 
                if ("TAG" in readlines):
                    _sw1 += readlines + "\n"
                if (".txt" in readlines):
                    IOT_line = Readtext.index(readlines) # To find the index of image overview text.
                if ("\ADR3" in readlines):
                    ADR3 =  Readtext.index(readlines)

            
            for i in range(SW_ID+3 , IOT_line+1):
                _sw += Readtext[i]
            
            path_sw = _sw.replace("\n", "").split("\\\\")
            lenght_ofpath = len(_sw.replace("\n", "").split("\\\\"))

            paths = "" #prd or dev and image overview text path will be stored.

            for pathsw in range(1, lenght_ofpath):
                paths += "\\\\"+path_sw[pathsw]+"\n"
            
            print(paths)


            _sw_list = ""

            for _swlist in range(IOT_line+1, ADR3+1):
                if ("\\bosch" in Readtext[_swlist]):
                    _sw_list += Readtext[_swlist].replace("\n", "") + Readtext[_swlist+1]
                else:
                    if ("ADR3" in Readtext[_swlist]):
                        pass
                    else:
                        _sw_list += Readtext[_swlist]
            print(_sw_list)

            tryout_mailfile.close()
            tryout_mailfile = open(f"{self.task_sw}.txt", 'r')
            
            Readtext1 = tryout_mailfile.read()
            start_Used = Readtext1.find("SW-ID") + len("SW-ID")

            # print (start_Used)
            end_ADR = Readtext1.find("\ADR3") + len("\ADR3")

            project_name_st = Readtext1.find("\ADR3") + len("\ADR3")
            project_name_en = Readtext1.find("PD Configuration ") + len("PD Configuration ")

            start_PD = Readtext1.find("PD Configuration ") + len("PD Configuration ")
            # print (start_PD)
            self.extracted_data1 = _sw1 + paths + _sw_list  #Readtext[start_Used :end_ADR]
            self.extracted_data2  = Readtext1[start_PD:].replace("\n", "").split("CD Configuration")
            print (self.extracted_data2)
            self.extracted_data3 = Readtext1[project_name_st: project_name_en]
         
            
        except FileNotFoundError:
            print (f"{self.task_sw}.txt is not found." )
            exit()



    def read_image_overview(self):

        base_path = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan"
        servers_location = ["0046","0047","0048", "0049"]
        sw_lnk_name = []
        image_name = []
        part_sw = {}
        self.emmc_details =[]
        self.part_details =[]
        self.Base_SWs = [] 
        self.sisterDevice = []
        self.GNSS = []

        for index in range(self.PrePartnumbers.count()):
            part_sw.update({self.PrePartnumbers[index]: self.baseSW[index]})
        #print ("The dictionart of the ds", part_sw)
    
        if (self.task_type == "SplUpd"):
            for (part_number, sw_name), suc_part in zip(part_sw.items(), self.part_number):
                for _location in servers_location:
                    sw_path = base_path + "\\" + _location + "_RN_AIVI_7513750800" + "\\00_SW\\_Versions\\" + sw_name + "\\IMX6\\"
                    if (os.path.exists(sw_path) == True):
                        sw_stamp = glob.glob(sw_path+"\\*.lnk")
                        sw_stamp = os.path.basename(str(sw_stamp))
                        sw_stamp = os.path.splitext(sw_stamp)[0]
                        sw_lnk_name.append(sw_stamp)
                        self.Base_SWs.append(str(sw_name[0:4]))
                        image_resides = base_path + "\\" + _location +"_RN_AIVI_7513750800" + "\\00_SW\\Production\\" +  str(sw_stamp) + "\\Release\\"
                        if (os.path.exists(image_resides)):
                            image_file = glob.glob(image_resides+"images_overview_" + sw_name[0:4] + ".txt")
                            #image_name.append(image_file)
                            image_file1 = str(image_file).replace("\\\\", "\\").replace("[","").replace("]", "").replace("'", "")

                            i = self._no_of_partnumbers
                            try:
                                # NeedToRun = "Y"
                                #for part_number in self.part_number:
                                #if (str(part_number) != "nan"): 
                                if ("A-IVI2" in  self.task_name or "CCS" in self.task_name or "P-IVI2" in self.task_name or "PIVI2" in self.task_name or "PIVI2" in self.task_name):
                                    pipe1 = subprocess.check_output(["perl", r"Fetch_from_FCID.pl", "-fcid", 'SWUPD_Tooling_'+ str(self.FCID_Ver) +'.xlsx', "-p" , part_number])
                                    Byte_To_String = str(pipe1)
                                    ValueOfDevice = re.search('Board_ID.+\(', Byte_To_String)
                                    GNSS_Value = re.search("GNSS.=.\w+", Byte_To_String)
                                    GNSS_Value = GNSS_Value.group(0).split("=")[1]
                                    self.GNSS.append(GNSS_Value)
                                else:
                                    GNSS_Value = ""
                                    self.GNSS.append(GNSS_Value)

                                if (str(part_number) != "nan"):  
                                    if (NeedToRun == "Y" or NeedToRun == "y"):
                                        #pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ str(self.FCID_Ver) +'.xlsx', "-hwlist", str(self.TO_HW_List), "-p" , part_number]) 
                                      
                                        
                                        #pipe = subprocess.run(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ str(self.FCID_Ver) +'.xlsx', "-hwlist", str(self.TO_HW_List), "-p" , part_number])          
                                        
                                       # pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", '
                                       # SWUPD_Tooling_'+ str(self.FCID_Ver) +'.xlsx', "-p" , part_number])
                                        
                                        
                                        cmd = [
                                            "perl",
                                            "tryout_devices.pl",
                                            "-fcid",
                                            f"SWUPD_Tooling_{self.FCID_Ver}.xlsx",
                                            "-hwlist",
                                            f"{self.TO_HW_List}",
                                            "-p",
                                            part_number
                                        ]

                                        try:
                                            result = subprocess.run(
                                                cmd,
                                                text=True,            # Decodes output to string
                                                capture_output=True,  # Captures both stdout and stderr
                                                check=True            # Raises CalledProcessError on non-zero exit
                                            )

                                            print("STDOUT:\n", result.stdout)
                                            print("STDERR:\n", result.stderr)

                                        except subprocess.CalledProcessError as e:
                                            print("Command failed with return code:", e.returncode)
                                            print("STDOUT:\n", e.stdout)
                                            print("STDERR:\n", e.stderr)

                                        

                                       # pipe = subprocess.check_output(f'perl tryout_devices.pl -fcid SWUPD_Tooling_{self.FCID_Ver}.xlsx -p {part_number}',shell=True,text=True )

                                        

                                        Byte_To_String = str(result.stdout)
                                        print("The Value of the Byte to String in the place of the all:", Byte_To_String)
                                        ValueOfDevice = re.findall('\|\^\_([^"]*)\_\^\|', Byte_To_String)
                                        if not ValueOfDevice:
                                            print ("Info: No sister device found!")
                                            SisterDevice = "No sister device found."
                                        else:
                                            SisterDevice = str(ValueOfDevice).replace("[", "").replace("\'","").replace("]", "")
                                    else:
                                        SisterDevice = "<<Manually add Sister Device>>"   

                                    #for part_number in self.part_number:                                    
                                    with open(image_file1, "r") as readiot:
                                        readlines_of_iot = readiot.readlines()
                                        count_of_iot = len(readlines_of_iot)
                                        for readeachline in range(count_of_iot):
                                            partnumber_line = readlines_of_iot[readeachline]
                                            #print ("partnumber_line", partnumber_line)
                                            
                                            _line_starts_with = partnumber_line.startswith(" ")
                                            store_readeachline = readeachline
                                            #if (_line_starts_with == True):
                                            if (part_number in readlines_of_iot[readeachline] and not "-> use" in readlines_of_iot[readeachline]):
                                                #print("readlines_of_iot[readeachline]", readlines_of_iot[readeachline].split(":")[0].strip())
                                                if (str(readlines_of_iot[readeachline].split(":")[0].strip()) == part_number):
                                                    if (readlines_of_iot[readeachline + 1].startswith(" ")):
                                                        partnumber_line = readlines_of_iot[readeachline]
                                                        _line_starts_with = partnumber_line.startswith(" ")
                                                        split_pn_line = partnumber_line.split(" ")
                                                        split_with_underscore = partnumber_line.split("_")
                                                        for sp_pn_line in split_pn_line:
                                                            match = re.search(part_number, sp_pn_line)
                                                            if match:
                                                                pn = sp_pn_line
                                                                s_pn = suc_part
                                                             

                                                            if ("emm" in sp_pn_line):
                                                                emmc = sp_pn_line
                                                                emmc_check = emmc

                                                            if ("PARTITION_SCHEM" in sp_pn_line):
                                                                map_cut1 = split_pn_line.index(sp_pn_line) + 1
                                                                map_cut = split_pn_line[map_cut1]
                                                                map_version = split_pn_line[map_cut1 + 1]
                                                        #self.part_details.append(pn + " " + map_cut + " "+ map_version)
                                                        self.part_details.append(s_pn + "(Pred : " +  pn.replace(":","") + " ) :" + " " + map_cut + " "+ map_version)
                                                        self.emmc_details.append(pn + " " + emmc) 
                                                        self.sisterDevice.append(pn + ":" + SisterDevice )
                                                        

                                                        check_reusage = 0
                                                        while (readeachline < count_of_iot):
                                                            if("-> use" in readlines_of_iot[readeachline]):
                                                                pattern = "\d.+\d"
                                                                reuse_partnumber = re.search(pattern, readlines_of_iot[readeachline])
                                                                if reuse_partnumber:
                                                                    reuse_pn = reuse_partnumber.group(0)
                                                                    print ("Reuse", reuse_pn)
                                                                #check Reuse and Input part number are same
                                                                if (str(reuse_pn) != str(part_number)):
                                                                    for checkReuse in range(count_of_iot):
                                                                        if (reuse_pn in readlines_of_iot[checkReuse] and not "-> use" in readlines_of_iot[checkReuse]):
                                                                            #print (readlines_of_iot[checkReuse])
                                                                            partnumber_line = readlines_of_iot[checkReuse]
                                                                            split_pn_line = partnumber_line.split(" ")
                                                                            #print (split_with_underscore[0])
                                                                            if ("emmc1" in partnumber_line.split("_")[0] and "emmc1" in  split_with_underscore[0]):
                                                                                for sp_pn_line in split_pn_line:
                                                                                    
                                                                                    match = re.search(reuse_pn, sp_pn_line)
                                                                                    if match:
                                                                                        pn = part_number
                                                                                    
                                                                                    # if ("emmc" in sp_pn_line):
                                                                                    if (emmc_check.split("_")[0] in sp_pn_line.split("_")[0]):
                                                                                        emmc = "{use:" + sp_pn_line + "}"
                                                                                        #print("Inside if Loop:", emmc)
                                                                                self.emmc_details.append(pn + " " + emmc) 

                                                                                
                                                                                break 
                                                                              
                                                                                                                                                    
                                                                            
                                                                            elif ("emmc2" in partnumber_line.split("_")[0] and "emmc2" in  split_with_underscore[0]):
                                                                                for sp_pn_line in split_pn_line:
                                                                                    
                                                                                    match = re.search(reuse_pn, sp_pn_line)
                                                                                    if match:
                                                                                        pn = part_number
                                                                                    
                                                                                    # if ("emmc" in sp_pn_line):
                                                                                    if (emmc_check.split("_")[0] in sp_pn_line.split("_")[0]):
                                                                                        emmc = "{use:" + sp_pn_line + "}"
                                                                                    # print("Inside if Loop:", emmc)
                                        
                                                                                self.emmc_details.append(pn + " " + emmc) 

                                                                                
                                                                                break 

                                                                            elif("emmc_" in partnumber_line and "emmc_" in emmc_check):
                                                                            #elif ("emmc" in partnumber_line.split("_")[0] and "emmc" in  split_with_underscore[0]):  
                                                                                for sp_pn_line in split_pn_line:
                                                                                    
                                                                                    match = re.search(reuse_pn, sp_pn_line)
                                                                                    if match:
                                                                                        pn = part_number
                                                                                    
                                                                                    # if ("emmc" in sp_pn_line):
                                                                                    if (emmc_check.split("_")[0] in sp_pn_line.split("_")[0]):
                                                                                        emmc = "{use:" + sp_pn_line + "}"
                                                                                        #print("Inside if Loop:", emmc)
                                        
                                                                                self.emmc_details.append(pn + " " + emmc) 
                                                                                break                                                                                                                                              
                                                                        
                                                                    break
                                                                break

                                                            readeachline = readeachline + 1



                                                    elif (readlines_of_iot[readeachline + 1].startswith(" ") != True):
                                                        if (part_number in readlines_of_iot[readeachline] and not "-> use" in readlines_of_iot[readeachline]):
                                                            partnumber_line = readlines_of_iot[readeachline]
                                                            _line_starts_with = partnumber_line.startswith(" ")
                                                            split_pn_line = partnumber_line.split(" ")
                                                            for sp_pn_line in split_pn_line:
                                                                match = re.search(part_number, sp_pn_line)
                                                                if match:
                                                                    pn = sp_pn_line
                                                                    s_pn = suc_part
                                                                
                                                                if ("emm" in sp_pn_line):
                                                                    emmc = sp_pn_line

                                                                if ("PARTITION_SCHEM" in sp_pn_line):
                                                                    map_cut1 = split_pn_line.index(sp_pn_line) + 1
                                                                    map_cut = split_pn_line[map_cut1]
                                                                    map_version = split_pn_line[map_cut1 + 1]

                                                                    #self.part_details.append(pn + " " + map_cut + " "+ map_version)
                                                                    self.part_details.append(s_pn + "(Pred : " +  pn.replace(":","") + " ) :" + " " + map_cut + " "+ map_version)
                                                                    self.emmc_details.append(pn + " " + emmc) 
                                                                    self.sisterDevice.append(pn + ":" + SisterDevice )
                                                                    #self.GNSS.append(GNSS_Value)
                                                    

                                        log.info (f"\n The Part Details as follows {self.part_details}" )
                                        log.info (f"\n THe Base SW = {self.Base_SWs}")
                                        


                                        self.part_details1 = [re_no_map for re_no_map in self.part_details if("No_Map ()" not in re_no_map) ]
                                     


                                        result = []
                                        [result.append(part_details) for part_details in self.part_details1 if part_details not in result]
            
                                        self.part_details1 = result

                                        print("The map details ",self.part_details1)
                                        log.info(f"The part details after result append Line: 496 {self.part_details1}")
                                else:
                                    pass
                            
                            except FileNotFoundError:
                                print ("\n Error: Images overview text might not be available, Please check \n")
                                log.info("\n Line: 797, Error: Images overview text might not be available, Please check \n")
                                exit()
                

                                                                
        else:
            for _location in servers_location:
                sw_path = base_path + "\\" + _location + "_RN_AIVI_7513750800" + "\\00_SW\\_Versions\\" + self.task_sw + "\\IMX6\\"
                if (os.path.exists(sw_path) == True):
                    sw_stamp = glob.glob(sw_path+"\\*.lnk")
                    sw_stamp = os.path.basename(str(sw_stamp))
                    sw_stamp = os.path.splitext(sw_stamp)[0]
                    sw_lnk_name.append(sw_stamp)
                    image_resides = base_path + "\\" + _location +"_RN_AIVI_7513750800" + "\\00_SW\\Production\\" +  str(sw_stamp) + "\\Release\\"
                    if (os.path.exists(image_resides)):
                        image_file = glob.glob(image_resides+"images_overview_" + self.task_sw[0:4] + ".txt") 
                        image_file1 = str(image_file).replace("\\\\", "\\").replace("[","").replace("]", "").replace("'", "")

                        i = self._no_of_partnumbers
                        try:
                            # NeedToRun = "Y"
                            for part_number, p_part_number in zip (self.part_number, self.PrePartnumbers):
                                if ("A-IVI2" in  self.task_name or "CCS" in self.task_name or "P-IVI2" in self.task_name or "PIVI2" in self.task_name):
                                    pipe1 = subprocess.check_output(["perl", r"Fetch_from_FCID.pl", "-fcid", 'SWUPD_Tooling_'+ str(self.FCID_Ver) +'.xlsx', "-p" , part_number])
                                    Byte_To_String = str(pipe1)
                                    ValueOfDevice = re.search('Board_ID.+\(', Byte_To_String)
                                    GNSS_Value = re.search("GNSS.=.\w+", Byte_To_String)
                                    GNSS_Value = GNSS_Value.group(0).split("=")[1]
                                    self.GNSS.append(GNSS_Value)
                                else:
                                    GNSS_Value = ""
                                    self.GNSS.append(GNSS_Value)


                                if (str(part_number) != "nan"):  
                                    if (NeedToRun == "Y" or NeedToRun == "y"):          
                                        pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ str(self.FCID_Ver) +'.xlsx', "-hwlist", str(self.TO_HW_List), "-p" , part_number])

                                        #pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ str(self.FCID_Ver) +'.xlsx', "-p" , part_number])

                                        Byte_To_String = str(pipe)

                                        ValueOfDevice = re.findall('\|\^\_([^"]*)\_\^\|', Byte_To_String)
                                        
                                       
                                        if not ValueOfDevice:
                                            print("Info: No Sister device found !")
                                            SisterDevice = "No Sister device found."
                                        else:
                                            SisterDevice = str(ValueOfDevice).replace("[", "").replace("\'","").replace("]", "")
                                    else:
                                        SisterDevice = "<<Manually add Sister Device>>"   

                                    with open(image_file1, "r") as readiot:
                                        readlines_of_iot = readiot.readlines()
                                        count_of_iot = len(readlines_of_iot)
                                        for readeachline in range(count_of_iot):
                                            partnumber_line = readlines_of_iot[readeachline]
                                            #print ("partnumber_line", partnumber_line)
                                            _line_starts_with = partnumber_line.startswith(" ")
                                            store_readeachline = readeachline
                                            #if (_line_starts_with == True):
                                            if (part_number in readlines_of_iot[readeachline] and not "-> use" in readlines_of_iot[readeachline]):
                                                #print("readlines_of_iot[readeachline]", readlines_of_iot[readeachline].split(":")[0].strip())
                                                if (str(readlines_of_iot[readeachline].split(":")[0].strip()) == part_number):
                                                    if (readlines_of_iot[readeachline + 1].startswith(" ")):
                                                        partnumber_line = readlines_of_iot[readeachline]
                                                        _line_starts_with = partnumber_line.startswith(" ")
                                                        split_pn_line = partnumber_line.split(" ")
                                                        split_with_underscore = partnumber_line.split("_")
                                                        for sp_pn_line in split_pn_line:
                                                            match = re.search(part_number, sp_pn_line)
                                                            if match:
                                                                pn = sp_pn_line
                                                                p_pn = p_part_number
                                                                

                                                            if ("emm" in sp_pn_line):
                                                                emmc = sp_pn_line
                                                                emmc_check = emmc

                                                            if ("PARTITION_SCHEM" in sp_pn_line):
                                                                map_cut1 = split_pn_line.index(sp_pn_line) + 1
                                                                map_cut = split_pn_line[map_cut1]
                                                                map_version = split_pn_line[map_cut1 + 1]
                                                        #self.part_details.append(pn + " " + map_cut + " "+ map_version)
                                                        self.part_details.append(pn.replace(":", "") + "(Pred: "+ p_pn + ") : " + " " + map_cut + " "+ map_version)
                                                        self.emmc_details.append(pn + " " + emmc ) 
                                                        self.sisterDevice.append(pn + ":" + SisterDevice )
                                                        

                                                        check_reusage = 0
                                                        while (readeachline < count_of_iot):
                                                            if("-> use" in readlines_of_iot[readeachline]):
                                                                pattern = "\d.+\d"
                                                                reuse_partnumber = re.search(pattern, readlines_of_iot[readeachline])
                                                                if reuse_partnumber:
                                                                    reuse_pn = reuse_partnumber.group(0)
                                                                    log.info (f"THE REUSE PN - {reuse_pn}")
                                                                #check Reuse and Input part number are same
                                                                if (str(reuse_pn) != str(part_number)):
                                                                    for checkReuse in range(count_of_iot):
                                                                        if (reuse_pn in readlines_of_iot[checkReuse] and not "-> use" in readlines_of_iot[checkReuse]):
                                                                            log.info (f"The line of which the resue partnumber is {readlines_of_iot[checkReuse]}")
                                                                            partnumber_line = readlines_of_iot[checkReuse]
                                                                            split_pn_line = partnumber_line.split(" ")
                                                                            #log.info (split_with_underscore[0])
                                                                            if ("emmc1" in partnumber_line.split("_")[0] and "emmc1" in  split_with_underscore[0]):
                                                                                for sp_pn_line in split_pn_line:
                                                                                    
                                                                                    match = re.search(reuse_pn, sp_pn_line)
                                                                                    if match:
                                                                                        pn = part_number
                                                                                    
                                                                                    # if ("emmc" in sp_pn_line):
                                                                                    if (emmc_check.split("_")[0] in sp_pn_line.split("_")[0]):
                                                                                        emmc = "{use:" + sp_pn_line + "}"
                                                                                        #print("Inside if Loop:", emmc)
                                                                                self.emmc_details.append(pn + " " + emmc) 

                                                                                
                                                                                break       
                                                                                                                                                    
                                                                            
                                                                            elif ("emmc2" in partnumber_line.split("_")[0] and "emmc2" in  split_with_underscore[0]):
                                                                                for sp_pn_line in split_pn_line:
                                                                                    
                                                                                    match = re.search(reuse_pn, sp_pn_line)
                                                                                    if match:
                                                                                        pn = part_number
                                                                                    
                                                                                    # if ("emmc" in sp_pn_line):
                                                                                    if (emmc_check.split("_")[0] in sp_pn_line.split("_")[0]):
                                                                                        emmc = "{use:" + sp_pn_line + "}"
                                                                                        # print("Inside if Loop:", emmc)
                                        
                                                                                self.emmc_details.append(pn + " " + emmc) 

                                                                                
                                                                                break 

                                                                            elif("emmc_" in partnumber_line and "emmc_" in emmc_check):
                                                                            #elif ("emmc" in partnumber_line.split("_")[0] and "emmc" in  split_with_underscore[0]):  
                                                                                for sp_pn_line in split_pn_line:
                                                                                    
                                                                                    match = re.search(reuse_pn, sp_pn_line)
                                                                                    if match:
                                                                                        pn = part_number
                                                                                    
                                                                                    # if ("emmc" in sp_pn_line):
                                                                                    if (emmc_check.split("_")[0] in sp_pn_line.split("_")[0]):
                                                                                        emmc = "{use:" + sp_pn_line + "}"
                                                                                        log.info(f"Inside if Loop:{emmc}")
                                        
                                                                                self.emmc_details.append(pn + " " + emmc) 
                                                                                break                                                                                                                                              
                                                                        
                                                                    break
                                                                break

                                                            readeachline = readeachline + 1

                                                    elif (readlines_of_iot[readeachline + 1].startswith(" ") != True):
                                                        if (part_number in readlines_of_iot[readeachline] and not "-> use" in readlines_of_iot[readeachline]):
                                                            partnumber_line = readlines_of_iot[readeachline]
                                                            _line_starts_with = partnumber_line.startswith(" ")
                                                            split_pn_line = partnumber_line.split(" ")
                                                            for sp_pn_line in split_pn_line:
                                                                match = re.search(part_number, sp_pn_line)
                                                                if match:
                                                                    pn = sp_pn_line
                                                                    p_pn = p_part_number
                                                                    

                                                                if ("emm" in sp_pn_line):
                                                                    emmc = sp_pn_line
                                                                    

                                                                if ("PARTITION_SCHEM" in sp_pn_line):
                                                                    map_cut1 = split_pn_line.index(sp_pn_line) + 1
                                                                    map_cut = split_pn_line[map_cut1]
                                                                    map_version = split_pn_line[map_cut1 + 1]
                                                            #self.part_details.append(pn + " " + map_cut + " "+ map_version)
                                                            self.part_details.append(pn.replace(":", "") + "(Pred: "+ p_pn + ") : " + " " + map_cut + " "+ map_version)
                                                            self.emmc_details.append(pn + " " + emmc) 
                                                            self.sisterDevice.append(pn + ":" + SisterDevice )
                                                            #self.GNSS.append(GNSS_Value)

                                            self.part_details1 = [re_no_map for re_no_map in self.part_details if("No_Map ()" not in 
                                            re_no_map) ]
                                        
                                        result = []
                                        [result.append(part_details) for part_details in self.part_details1 if part_details not in result]
            
                                        self.part_details1 = result

                                                                                            
                                else:
                                    pass
                         
                        except FileNotFoundError:
                            print ("\n Error: Images overview text might not be available, Please check \n")
                            log.info ("\n Error: Images overview text might not be available, Please check \n")
                            exit()
    
        log.info(f"The sister device, line: 676 - {self.sisterDevice} ", )
        _sisDevice = []
        for _sisdev in self.sisterDevice:
            if (_sisdev not in _sisDevice):
                _sisDevice.append(_sisdev)
            else:
                log.info("Duplicate value found in the sis device")
            

        

        self.sisterDevice = _sisDevice

        log.info ("After the Duplicate removed in the sis device {_sisDevice}" )

        log.info(f"The sister device, line: 722 - {self.sisterDevice}")


        log.info (f"The part details before calling set function, Line: 725 - {self.part_details}")

        self.part_details = set(self.part_details)
        self.part_details = list(self.part_details)

        log.info (f"The part details after calling set function, Line: 721 - {self.part_details}")

        log.info ("\n \t")
        log.info (f"Checking the emmc usage before- {self.emmc_details}")
        log.info ("\n \t")
 

    
    def getData_Jira(self):
            
            hyper_flash = {
                "030D11" : ["CPLD_PEXT_SBR_PM02", "flash_image_nissan-aivi2-c3-3gb.bin"],
                "030E11" : ["CPLD_PEXT_SBR_PM02", "flash_image_nissan-aivi2-c3.bin"],
                "031311" : ["CPLD_PEXT_SBR_M3_J32V_PM01", "flash_image_nissan-aivi2-j32v-c0.bin"],
                "031511" : ["CPLD_PEXT_SBR_LATTICE_PM02", "flash_image_nissan-aivi2-c3-cpld.bin"],
                "031811" : ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-b.bin"],
                "031611" : ["CPLD_PEXT_SBR_M3_CCS11_PM01", "flash_image_nissan-aivi2-ccs11-b.bin"],
                "031411" : ["CPLD_PEXT_SBR_LATTICE_PM02", "flash_image_nissan-aivi2-c3-3gb-cpld.bin"],
                "031711" : ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-b-3gb.bin"],
                "030F11" : ["CPLD_PEXT_SBR_M3_CCS11_PM01","flash_image_nissan-aivi2-b-3gb.bin"],
                "031111" : ["CPLD_PEXT_SBR_M3_J32V_PM01","flash_image_nissan-aivi2-b-3gb.bin"],
                        }
            
            with open(f"{self.task_sw}.txt", 'r') as fp:
                _file = fp.readlines() 
                if(self.task_type == "SplUpd"):
                    
                    for stickpath in _file:
                        if (stickpath.startswith("<< Please update the Stick Manually >>")):
                            find_Stick = _file.index(stickpath)
                            stick_index =  _file[find_Stick]
                            verify_stick = stick_index.strip().replace("\n","")
                            break
                        
                        elif(stickpath.startswith(r"\\bosch.com")):
                            find_Stick = _file.index(stickpath)
                            find_stick_bosch = find_Stick + 1
                            stick_index =  _file[find_Stick] + _file[find_stick_bosch] + _file[find_Stick + 2]
                            print ("we",stick_index)
                            verify_stick = stick_index.strip().replace("\n","")
                            ''' if (verify_stick.split("\\")[-1] == 'stic'):
                                print("Stick reforming.")
                                stick_index =  _file[find_Stick] + _file[find_stick_bosch] + _file[find_Stick + 2]
                                verify_stick = stick_index.strip().replace("\n","")
                            '''
                            print ("The Verify Stick path :- ", verify_stick)
                            break
                else:
                    verify_stick = ""
                    
                                                        
                
            split_taskname = self.task_name.split()
            try:

                iss_upd = self.BoschJira.issue(self.to_task_issue_id)
            except:
                print ("\n Error:  Please check the Tryout Task ID in the init. ")
                exit()
 

            for find_dev_prd in split_taskname:
                if ("TSB" in find_dev_prd or "DSB" in  find_dev_prd):
                    dev_prd = "DEV"
                    break
                else:
                    dev_prd = "PRD"
            for splitname in split_taskname:
                if ("A-IVI2" == splitname or "CCS" == splitname or "CCS1.1" == splitname or "CCS 1.5" == splitname or "P-IVI2" == splitname or "PIVI2" == splitname):
                    table_header = "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||" + "\n"
                    number_of_rows = self._no_of_partnumbers
                    number_of_columns = 6
                    break
                elif ("P-IVI" == splitname):
                    table_header = "||HW||BoardID||Image||owned by||SW; Remarks||" + "\n"
                    number_of_rows = self._no_of_partnumbers
                    number_of_columns = 5
                    break                
                else:
                    table_header = "||HW||BoardID||Image||owned by||SW; Remarks||" + "\n"
                    number_of_rows = self._no_of_partnumbers
                    number_of_columns = 5 
            if(self.task_type == "SplUpd"):               
                pn_con      =   list(self.PrePartnumbers)
                pn_con_1    =   list(self.part_number)
            else:
                pn_con      =   list(self.part_number)
                pn_con_1    =   list(self.PrePartnumbers)
            # print (pn_con)
            # print ("Emmc detailss ", self.emmc_details)


            print ("The GNSS Values for ", self.GNSS)
            result_dict = {pn: [] for pn in pn_con}

            # print("The Result Dict :", result_dict)
            log.info(f"The Result Dict - {result_dict}")
            
            #self.emmc_details = set(self.emmc_details)

            #print ("\n \n \n \t Before emmc_detials =", self.emmc_details)
            log.info(f"\n \n \n \t Line:803, Before emmc_details = {self.emmc_details}")
            #Removing duplicate entries using the List Comprehension            
            result = []
            [result.append(emmc_details) for emmc_details in self.emmc_details if emmc_details not in result]
            
            self.emmc_details = result

            
            log.info(f"\n \n \n \t After emmc_detials = {self.emmc_details}")


            # Iterate over each item in the 'lists'
            for item in self.emmc_details:
                # print("ITEMS.", )
                log.info(f"The items in the emmc_details using for loop as listed: {item}")
                for pn in pn_con:
                    if (pn != "nan"):
                        if item.startswith(pn):
                            result_dict[pn].append(item.split(' ')[1])
                       
                            break  # Stop searching further once a match is found


            log.info(f"\n The result dictionary values as {result_dict.items()}")

            print ("Checking the result of the items in the of the dictionary. \n \n")
            print(result_dict.items())

            # Output the result
            for pn, values in result_dict.items():
                log.info(f'\n \n Info: Values for PN {pn}: {values} \n \n')

            dict_list = list(result_dict.items())
            log.info(f"Tthe dict result, Line: 831 as {dict_list}")

            emmces = []

            BoardID = ""

            for pnc in pn_con:
                if (str(pnc) != "nan"):
                    for emmc_Details in self.emmc_details:
                        if (pnc in emmc_Details):
                            emmces.append(emmc_Details)                                                                                         

            # print ("The Emmcs", emmces)
            #print ("Befor Nan:", result_dict) 

            new_dict = {}
            for key, value in result_dict.items():
                if not isinstance(key, float) or not math.isnan(key):
                    new_dict[key] = value

            #print("The New_Dict", new_dict)
            log.info(f"The new dictionart in the new_dict, {new_dict}")
            result_dict = new_dict
            rows = "|" 
            for row in range(len(result_dict)):
                
                #for col in range(len(result_dict)):
                try:
                    print (str(dict_list[row]))
                    mapping_table = str.maketrans({'[': '', ']': '', ',': '', "'": '', ')' : "", '(' : ""}) 
                    #part_numbers = str(dict_list[row]).split('[')[0].replace("'", "").replace("(","").replace(",", "")
                    part_numbers = str(dict_list[row]).split('[')[0].translate(mapping_table)
                    print("The Book to Part Numbers", part_numbers)
                    sis_Dev_split = self.sisterDevice[row].split("::")

                    log.info (f"Part - {part_numbers.strip()} - SIS {sis_Dev_split[0].strip()}")

                    print (f"Part - {part_numbers.strip()} - SIS {sis_Dev_split[0].strip()}")

                    if(part_numbers.strip() == sis_Dev_split[0].strip()):
                        sister_Devices = self.sisterDevice[row]
                    else:
                        sister_Devices = "Not known"
                    gnss_value = self.GNSS[row]
                    print (gnss_value)
                    
                    #emmc_partnumber = str(dict_list[row]).split('[')[1].replace("'", "").replace(")","").replace(",", "").replace("]", "")
                    emmc_partnumber = str(dict_list[row]).split('[')[1].translate(mapping_table)
                    # print("DICT:2", emmc_partnumber)
                    #print ("COLC ", emmc_partnumber)
                    emmc_ID         = str(dict_list[row]).split('_')[1].translate(mapping_table)
                    # print ("DICT:3", emmc_ID)
                    #print ("COLC ", emmc_ID)
                except IndexError:
                    print ("ERROR: ", "Please recheck either Part Numbers or SW is incorrect or invalid in the init. ")
                    log.error(f"ERROR: Please recheck either Part Numbers or SW is incorrect or invalid in the init.")
                    exit()

                if(self.task_type == "SplUpd"):
                    SW_IN_Description =  self.Base_SWs[row]
                    check_partnumber = self.PrePartnumbers[row]
                    #SW_IN_Description =  Base_SWs"{color:#DE350B}" + str(self.baseSW[0]).split('_')[0]  + "{color}"
                
                else:
                    SW_IN_Description = str(self.task_sw).split('_')[0]  
                    check_partnumber = self.part_number[row]
        
                if ("P-IVI" == splitname):
                    if (part_numbers.strip() == check_partnumber):
                        if(self.task_type == "SplUpd"):
                            partNumber_Details = f"{self.part_number[row]} ( Pred: {part_numbers.strip()}) "
                        else:
                            partNumber_Details = f"{self.PrePartnumbers[row]} ( Pred: {part_numbers.strip()})"

                        rows += f"|*{partNumber_Details}* \n *Sister Device:* \n, ({sister_Devices}) | {(str(emmc_ID))} | {emmc_partnumber}|[~mkr2hi]| SW_{SW_IN_Description}_{dev_prd}; \n \
TryOut: (?)(?) \n \
Config: (?) \n \
CheckSums: (?) \n \
DS: (?) \n  |"     
                elif ("A-IVI2" == splitname or "CCS" == splitname or "CCS1.1" == splitname or "CCS 1.5" == splitname or "P-IVI2" == splitname or "PIVI2" == splitname):
                    if (part_numbers.strip() == check_partnumber):
                        if(self.task_type == "SplUpd"):
                            partNumber_Details = f"{self.part_number[row]} (Pred: {part_numbers.strip()})"
                        else:
                            partNumber_Details = f"{self.PrePartnumbers[row]} (Pred: {part_numbers.strip()})"
                        
                        rows += f"|*{partNumber_Details}* \n *Sister Device:* \n, ({sister_Devices})|{(str(emmc_ID))} | {hyper_flash[str(emmc_ID)][1]} | {emmc_partnumber}| {gnss_value} / {hyper_flash[str(emmc_ID)][0]} | SW_{SW_IN_Description}_{dev_prd}; \n \
TryOut: (?)(?) \n \
Config: (?) \n \
CheckSums: (?) \n \
DS: (?) \n  |"                    
                else:
                    if (part_numbers.strip() == check_partnumber):
                        if(self.task_type == "SplUpd"):
                            partNumber_Details = f"{self.part_number[row]} (Pred: {part_numbers.strip()})"
                        else:
                            partNumber_Details = f"{self.PrePartnumbers[row]} (Pred: {part_numbers.strip()})"                    
                    rows += f"|*{partNumber_Details}* \n *Sister Device:* \n ({sister_Devices})|{(str(emmc_ID))} | {emmc_partnumber}|[~mkr2hi]| SW_{SW_IN_Description}_{dev_prd}; \n \
TryOut: (?)(?) \n \
Config: (?) \n \
CheckSums: (?) \n \
DS: (?) \n  |"     

            #     rows +=  "|" 
                
            # table_header += rows + "\n"
            
                if ("A-IVI2" == splitname or "CCS" == splitname or "CCS1.1" == splitname or "CCS 1.5" == splitname or "P-IVI2" == splitname or "PIVI2" == splitname):
                    BoardID += f"*{(str(emmc_ID))}* : {hyper_flash[str(emmc_ID)][1]} " + "\n"
                   


            rows +=  "|" 
                
            table_header += rows + "\n"

            
            # mapping_table = str.maketrans({'[': '', ']': '', ',': '', "'": '', "\\n": '"\n"'})                
            
           # print(f"the splitted {BoardID}", type(BoardID))
            if (self.task_type == "SplUpd"):
                summary = "Perform Reflash Try-Out with SW " + str(self.task_sw) + f" ({self.task_name})"
                compatibility_matrix = "*Compatibility Matrix:-* \n"
            else:
                summary = "Perform Internal Try-Out with SW " + str(self.task_sw) + f" ({self.task_name})"
                compatibility_matrix = ""

            if ("P-IVI2" in self.task_name or "PIVI2" in self.task_name):
                note_sw = "*Note:*"
                scope = "P-IVI2"
                Board_Note = "BoardID – Hyperflash file name assignment for the release to production \n"
            elif("P-IVI" in self.task_name):
                note_sw = ""
                scope = "Sc2.1"
                Board_Note = " "
            elif("CCS1.1" in self.task_name):
                note_sw = "*Note:*"
                scope = "CCS1.1"
                Board_Note = "BoardID – Hyperflash file name assignment for the release to production \n"
            elif ("A-IVI2" in self.task_name):
                note_sw = "*Note:*"
                scope = "A-IVI2"
                Board_Note = "BoardID – Hyperflash file name assignment for the release to production \n"
            elif ("MMC" in self.task_name and  "CCS 1.5" in self.task_name or "CCS1.5" in self.task_name):
                note_sw = "*Note:*"
                scope = "M-IVI2"
                Board_Note = "BoardID – Hyperflash file name assignment for the release to production \n"
            else:
                note_sw = ""
                scope = "A-IVI"
                Board_Note = ""

            iss_upd.update(fields={'summary': summary,'customfield_10042' : f"h5.SW {self.task_sw}"+ "\n"+ "Used for " + self.task_issue_id + " "+ self.task_name + "{code:java}" + self.extracted_data1 + "{code}" +  self.extracted_data3.replace("PD Configuration", "")  +"{code:java}" + "PD Configuration    " + self.extracted_data2[0] + "\n" + "CD Configuration    " + self.extracted_data2[1] +"{code}", 'description' : "{code:java}" + self._jiradescription +"{code}" + scope + " - " + self.task_type +  " TryOut\n"  + "USB-Stick:" + "\n" + verify_stick +
            '''\n
                PD-Stick: -
                CD_DEF-Stick: -
                Map :- \n'''+ "\n".join(self.part_details1) + "\n" + "\n" + compatibility_matrix + "{color:#ff0000}Work-A-Round for Production required{color}: No \n"+ table_header  + "\n" + note_sw + "\n" + Board_Note  +  BoardID + "\n" + "Checksums: https://hi-dms.de.bosch.com/docushare/dsweb/View/Collection-" + str(self.Collection_ID).replace('.0', '') }              
                )
            print ("\n *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** \n ")
            print (f"\n \033[95m  Jira task {self.to_task_issue_id} is updated with SW {self.task_sw} \033[00m \n")
            print ("\n *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** \n ")  
            log.info(
                f'''
                    \n *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** \
                    \n  \033[95m Jira task \033[95m  {self.to_task_issue_id} \033[00m is updated with SW \033[95m  {self.task_sw}  \033[00m \n 
                    \n *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** \n
                '''
            )
    
    def destroy_txtfile(self):
        if os.path.isfile("jira_issue_extraction.txt"):
            os.remove(f"jira_issue_extraction.txt")
        if os.path.isfile("jira_extracted_inputs.txt"):
            os.remove(f"jira_extracted_inputs.txt")
        #if os.path.isfile(f"{self.task_sw}.txt"):
         #   os.remove(f"{self.task_sw}.txt")
                                    
            
if __name__ == "__main__":
   print (f"Create Tryout task Jira Version : {__version}")
   log.info(f"Create Tryout task Jira Version : {__version}")
   main_obj=Jira_issue_create()
   main_obj.readCSV_InputFile()
   main_obj.set_inputs()
   #main_obj.get_inputs()
   main_obj.extract_description()
   main_obj.read_tryoutMail()
   main_obj.read_image_overview()
   main_obj.getData_Jira()
   #main_obj.destroy_txtfile()
# -*- coding: utf-8 -*-
r"""
Crafting started on 02-03-2023 @ 13:24 

By Creator: Kumaran Sekar (MS\ECR4-XC); (EUJ1COB);

Changes:
13-03-2023, 1.  Tryout mail for Image Release will be generated.
20-03-2023, 2.  Extended to Special Update for AIVI
04-08-2023, 3.  Sister device finding is implemented and Path formation from server (0046 to 0049)
10-08-2023, 4.  WO_Privatekey path for Renault is added when the task is Without private key and fixed image path navigation error.
10-08-2023, 5.  getpass method is implemented to get the password securely for jira access.
23-08-2023, 6.  Fixes the issue related to Reflash and add the V850, TestManager Version in the mail.
25-08-2023, 7.  Copying of PD, CD, V850 and ADR is included in this script.
03-10-2023, 8.  Extended to Support for GEN4 image and special update.
21-11-2023, 9.  Bug Fixes (Incorrect Subject Name) and added a condition to check the shortcut path to navigate and take the IOT file.
29-11-2023, 10. Fixed reading the bosch xml from Base SW to Main SW.
06-12-2023, 11. Adapted the migration of jira to tracker for reading the issues.
08-12-2023, 12. Improvement made to authenticate the Tracker using Personal Access Token.
04-04-2024, 13. Scope P-IVI2 is added
09-04-2024, 14. Inherited the Jira Creation and added a print for Tryout Mail Generator.
24-06-2024, 15. Tryout Mail Generator and Jira creation is integrated and fixes major, minor issues.
01-09-2024, 16. Integrated of Sister Device fetching and reuse image for the part numbers is added in the jira description.
03-09-2024, 17. Bug fixes.
27-11-2024, 18. Gnss and other corner issues are fixed, 98% Stable in this point this build.
12-08-2025, 19. Device conversion check by reading the FCID tables using part number and its map.
12-08-2025, 20. Printing notifcation message for device conversion use.
19-08-2025, SyntaxWarning fix for python above 3.12
19-08-2025, Stick path is fixed. Earlier in some cases, the stick is coming as "stic". It is fixed with proper joints.
23-09-2025, Device Preparation for reflash is added.
31-10-2025, Successor and Predecessor Part number organized based on release type.
13-11-2025, Fix provided in the create_tryout_jirs_task.py
"""
import datetime
from pathlib import Path
import shutil
import pandas as pd
import re
import win32com.client as win32
import os
import glob
import xml.etree.ElementTree as ET
import subprocess
  #Importing the required dependencies:
#from jira import JIRA
import urllib3
import ServerPath_File as SPF
from create_tryout_jira_task import Jira_issue_create
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging as log
from logging import handlers
from JiraAccess import jira_access

global _readInputFile
global JiraUrl
global jira_url_browse
global warn_map
global warn_part

# Define color codes
RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
LightBlue = '\033[96m'
CYAN = '\033[93m'
RESET = '\033[0m' # Resets color and style

#log_file creation:

handlers.TimedRotatingFileHandler(filename="tryout_mail_generator.log", when='M', interval=1, backupCount=4, encoding=None, delay=False, utc=False, atTime=datetime.datetime.now(), errors=None)

log.basicConfig(filename="tryout_mail_generator.log", level=log.INFO, format='%(asctime)s, %(message)s', datefmt = '%Y-%m-%d %H:%M:%S' , encoding="UTF-8" )


_version = "01.10"



NeedToRun = SPF.PathFormation.NeedToRun
AskToCopy = SPF.PathFormation.AskToCopy

JiraUrl = "https://rb-tracker.bosch.com/tracker05"
jira_url_browse  = "https://rb-tracker.bosch.com/tracker05/browse/"

class ReadCsv:

    def readCSV_InputFile():
        #dfInit = pd.read_csv("init.csv")
        #dfInit = pd.read_excel("init.xlsx",sheet_name="ValidSheet")
        dfInit = pd.read_excel("init.xlsx")        
        return dfInit

    def readCSV_Header():
        _readInputFile = ReadCsv.readCSV_InputFile()
        PartNumbers = _readInputFile['Part_Numbers']
        Predecessor_PN = _readInputFile['Predecessor_PN']
        SWVersion = _readInputFile['SW_Version']
        ReleaseTask = _readInputFile['Jira_Main_Task ']
        TOSubTask = _readInputFile['Jira_TO_Task']
        PDVer = _readInputFile['PD_Version']
        CDVer = _readInputFile['CD_Version']
        Header7 = _readInputFile['ProductType']
        ReleaseType = _readInputFile['Release_Type']
        BaseSW = _readInputFile['Base_SW']
        Docushare_CID = _readInputFile['Docushare_CollectionID']
        Tryout_cob = _readInputFile['Tryout_Location']
        FCID_Ver = _readInputFile['FCID_Version']
        HW_List = _readInputFile['HW_List']
        Private_Key = _readInputFile['Private_Key']
        Jira_username = _readInputFile['Jira_Access_Token']
        Task_Name = _readInputFile['Task_Name']
        Base_SW_Task = _readInputFile['BaseSW_Task']
        return PartNumbers, SWVersion, ReleaseTask, TOSubTask, PDVer, CDVer, Header7, BaseSW, ReleaseType, Docushare_CID, Tryout_cob, FCID_Ver, HW_List, Private_Key, Jira_username, Task_Name,Predecessor_PN, Base_SW_Task
        #          1            2       3               4       5       6       7       8       9           10                11           12        13       14          15            16  17
p1 = ReadCsv.readCSV_Header()
# Credentials = ReadCsv.readCredentials_InputFile()


class JiraCall:
    def getData_Jira():
        try:    
            BoschJira = jira_access()     
            issue = BoschJira.issue(p1[2][0])
            issue_summary = issue.fields.summary
            issue_description = issue.fields.description
            return issue_summary, issue_description
        except:
            print ("Maybe the Personal Access Token is expired.")

j1 = JiraCall.getData_Jira()
j2 = j1[1]

j1 = j1[0]

class InputReader:
    
    def getInputFromCSV():
        InputReader.Sw_Version = str(p1[1][0]) #input("Please enter the SW Version: ")
        InputReader.ReflashSw = str(p1[7][0])
        JiraMainTask = str(p1[2][0]) #input("Please enter the Jira Main Task ID: ")
        JiraSubTask = str(p1[3][0]) #input("Please enter the Jira Sub Task ID: ")
        
        return InputReader.Sw_Version, JiraMainTask, JiraSubTask,InputReader.ReflashSw
    
    def compare_search_partnumbers():
        #df_init = pd.read_excel(r"init.xlsx")
        df_FICD = pd.read_excel(f"SWUPD_Tooling_{p1[11][0]}.xlsx")

        successor_row  = []
        predecessor_row = []
        map_data_suc =[]
        map_data_pre = []        
        count = 0

    #for spn,ppn in zip(p1[0],p1[16]):
        for spn in p1[0]:
            #print("The part list is", df_FICD.iloc[:,28])
            found_match = False
            for iloc_part in df_FICD.iloc[:,28]:
                count = count + 1
                if (str(spn) in str(iloc_part)):
                    exact_SPN = str(iloc_part).split(",")
                    for exactPN in exact_SPN:
                        if (str(spn) == exactPN.replace("\n","")):
                            successor_row.append(count)
                            print("Exact_Count SPN", count-1)
                            map_data_suc.append(df_FICD.iloc[count-1][21])
                            found_match = True
                            break
                    if found_match:
                        break
            if not found_match:
                successor_row.append("None")
                map_data_suc.append("None")
                
                
            count = 0 #resetting the value
        
        count_1 = 0   
        for ppn in p1[16]:
            if (str(ppn) !=  "nan"):
                found_match1 = False 
                for iloc_part in df_FICD.iloc[:,28]:
                    count_1 = count_1 + 1
                    if (str(ppn) in str(iloc_part)):
                        exact_PPN = str(iloc_part).split(",")
                        for exactPPN in exact_PPN:
                            if (str(ppn) == exactPPN.replace("\n","")):
                                predecessor_row.append(count_1) 
                                print("Exact_Count PPN ", count_1-1)
                                map_data_pre.append(df_FICD.iloc[count_1-1][21])
                                found_match1 = True
                                break
                        if found_match1:
                            break
                            
                if not found_match1:
                    predecessor_row.append("None")
                    map_data_pre.append("None")
                    
            count_1 = 0 # resetting
            
              
        print (map_data_suc)
        print(successor_row)
        print (predecessor_row)
        print (map_data_pre)

        iterator = 0
        not_same_part = 0
        for i,j in zip(successor_row,predecessor_row):
            if (i == j):
                print (f"{GREEN}Nofication : Successor {p1[0][iterator]} and Predecessor {p1[16][iterator]} part numbers are in the same row at FCID.{RESET}")
                iterator = iterator + 1
            elif (i == "None" or j == "None"):
                print (f"{CYAN}Nofication : Either Successor {p1[0][iterator]} or Predecessor {p1[16][iterator]} part numbers are not in the FCID.{RESET}")
                iterator = iterator + 1

            else:
                print (f"{RED} Warning: The Successor {i} and Predecessor {j} Part numbers are not in the same row at FCID.{RESET}")
                not_same_part = not_same_part + 1
                
                

        iterator = 0
        not_same_map = 0
        base_counter = 0
        DevicePreparation_Content = ""
        _noStickPathNeeded = 0

        #for base_count in p1[7]:
        for i,j in zip(map_data_suc,map_data_pre):
            if (i == j):
                print (f" {GREEN} Nofication : Successor map data '{i}' for {p1[0][iterator]} and Predecessor map data '{j}' for  {p1[16][iterator]} are same {RESET}")
                iterator = iterator + 1  
                DevicePreparation_Content+= "<br>  <FONT COLOR='RED'> Device preparation: </FONT> SW "  + str(p1[7][base_counter]) + " See " + "<a href = " + jira_url_browse + str(p1[17][base_counter])  + ">" + str(p1[17][base_counter]) +  "</a>" + "<br>"
            elif (i == "None" or j == "None"):
                print (f"{CYAN}Nofication : Either Successor {p1[0][iterator]} or Predecessor {p1[16][iterator]} part numbers are not in the FCID.{RESET}")
                iterator = iterator + 1   
                DevicePreparation_Content+= "<br>  <FONT COLOR='RED'> Device preparation: </FONT> SW "  + str(p1[7][base_counter]) + " See " + "<a href = " + jira_url_browse + str(p1[17][base_counter])  + ">" + str(p1[17][base_counter]) +  "</a>" + "<br>"         
            else:
                print (f"{RED} Warning: The Successor {p1[0][iterator]} and Predecessor {p1[16][iterator]} map data are not same in FCID. {RESET}")
                iterator = iterator + 1
                
                if (i == "No_Map" and "7.50" in i):
                    DevicePreparation_Content+= "<br>  <FONT COLOR='RED'> Device preparation: </FONT> SW "  + str(p1[7][base_counter]) + " See " + "<a href = " + jira_url_browse + str(p1[17][base_counter])  + ">" + str(p1[17][base_counter]) +  "</a>"  + " -> Config update for SW "+ str(p1[1][0]).split("_")[0] + "-> " + " Stick update " + "( " + "SW " + str(p1[1][0]).split("_")[0] +" )" + "<br>"
                else:
                    DevicePreparation_Content+= "<br>  <FONT COLOR='RED'> Device preparation: </FONT> SW "  + str(p1[7][base_counter]) + " See " + "<a href = " + jira_url_browse + str(p1[17][base_counter])  + ">" + str(p1[17][base_counter]) +  "</a>"  + " -> Config update for SW "+ str(p1[1][0]).split("_")[0] + "-> " + " Stick update " + "( " + "SW " + str(p1[1][0]).split("_")[0] +" )" + " ->  WA to remove the existing MAP " + "(" + str(i) +  ")"  + " -> "+ "Map Update " + "(" +  str( j ) +")" + "<br>"
            base_counter  = base_counter + 1

    

        return map_data_suc, map_data_pre, not_same_part, not_same_map, DevicePreparation_Content, _noStickPathNeeded
    

    
    def inputPath_parser():
        InputReader.MainTask = "<a href = " + jira_url_browse + str(i1[1]) + ">" + str(i1[1]) + " " + str(j1) + "</a>"
        InputReader.SubTask = "<a href = " + jira_url_browse + str(i1[2])  + ">" + str(i1[2]) +  "</a>"  
                 
        #PDC_in = str(p1[4][0]) #input("Please enter the PD Configuration : ")
        #CDC_in = str(p1[5][0]) #input("Please enter the CD Configuration : ")
        #Lists
        ReleaseScope = ["aivi", "aivi2"]
        AIVI_Type = ["npivi", "rivie", "rnaivi"]
        AIVI2_Type = ["npivi2", "rivie2", "rnaivi2", "mmcivi2"]

        ConfigPDServerPath = str(SPF.PathFormation.PDConFigPath)
        ConfigCDServerPath = str(SPF.PathFormation.CDConFigPath)
        PathF = str(SPF.PathFormation.Prod_Path) #SPF.PathFormation.ProductionPath()
        ImagePath = str(SPF.PathFormation.ImagePath) #SPF.PathFormation.ImageOverViewFile()


        boschPath = str(SPF.PathFormation.BoschXML)
        RepoPath = str(SPF.PathFormation.Repo_Path)
        ServerComPath = str(SPF.PathFormation.ServerCPath)
        path_reflash = SPF.PathFormation.Prod_RF_Path

        InputReader.Production_Path = PathF
        InputReader.Reflash_Path = path_reflash

        if (str(p1[8][0]).startswith("SplUpd")):
            InputReader.imageOverview_Path = ""
            
            base_path = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan"
            servers_location = ["0046","0047","0048", "0049"]
            sw_lnk_name = []
            #image_name = []
            part_sw_IMAGE = []
            #emmc_details =[]
            #part_details =[]
            #resultCmp = []
            #resultList = []

            for index in range(p1[16].count()):
                part_sw_IMAGE.append(p1[7][index])
            log.info(f"The dictionary of the data servers {part_sw_IMAGE}" ) 

            for sw_name in part_sw_IMAGE:

                for _location in servers_location:
                    sw_path = base_path + "\\" + _location + "_RN_AIVI_7513750800" + "\\00_SW\\_Versions\\" + sw_name + "\\IMX6\\"
                    if (os.path.exists(sw_path) == True):
                        sw_stamp = glob.glob(sw_path+"\\*.lnk")
                        sw_stamp = os.path.basename(str(sw_stamp))
                        sw_stamp = os.path.splitext(sw_stamp)[0]
                        sw_lnk_name.append(sw_stamp)
                        image_resides = base_path + "\\" + _location +"_RN_AIVI_7513750800" + "\\00_SW\\Production\\" +  str(sw_stamp) + "\\Release\\"
                        if (os.path.exists(image_resides)):
                            image_file = glob.glob(image_resides+"images_overview_" +sw_name[0:4]+ ".txt")
                            #image_name.append(image_file)
                            image_file1 = str(image_file).replace("\\\\", "\\").replace("[","").replace("]", "").replace("'", "")
                            InputReader.imageOverview_Path += image_file1 + "\n"
            
        else:        
        
            #Getting the Shortcut Software timestamp name from the production folder:
            for x in os.listdir(InputReader.Production_Path):
                if (len(str(x)) == 17):

                    if x.endswith(".lnk") and x.__contains__("_"):
                        # Prints only text file present in My Folder
                        InputReader.Filename = Path(x).stem
                        #print(InputReader.Filename)
                else:
                    print ("Please check the SW Shortcut path")

            # search all files inside a specific folder
            # *.* means file name with any extension
            dir_path = ImagePath
            log.info(f"The directory path is {dir_path} \n")
            dir_path = dir_path.replace("SW_ID", InputReader.Filename )
            log.info(f"The directory path after replace {dir_path} \n")
            
            for file in glob.glob(dir_path, recursive=True):
                InputReader.imageOverview_Path = file

        if (str(p1[8][0]).startswith("SplUpd")):

            bosch_xmlPath = str(SPF.PathFormation.RF_BoschXML_Path)
          

            for x in os.listdir(InputReader.Reflash_Path):
                if (len(str(x)) == 17):

                    if x.endswith(".lnk") and x.__contains__("_"):
                        # Prints only text file present in My Folder
                        InputReader.Filename_bosch = Path(x).stem
                        log.info(f"The image file - {InputReader.Filename_bosch}")
                else:
                    print ("Please check the SW Shortcut path")   
        else:
                 bosch_xmlPath = boschPath


        if ("A-IVI2" in j1 or "CCS" in j1 or "P-IVI2" in j1):
            if ("P-IVI" in j1 or "PIVI" in j1):
                for rt in ReleaseScope:
                    if (rt == "aivi2"):   
                        for rs in AIVI2_Type:
                            if (rs == "npivi2"):
                                bosch_xml_path = str(bosch_xmlPath) + "\\" + str(rt) + r"\stick" + "\\" + str(rs) + r"\bosch.xml"
            elif ("Renault" in j1):
                for rt in ReleaseScope:
                    if (rt == "aivi2"):   
                        for rs in AIVI2_Type:
                            if (rs == "rivie2"):
                                bosch_xml_path = str(bosch_xmlPath) + "\\" + str(rt) + r"\stick" + "\\" + str(rs) + r"\bosch.xml"
            elif ("Nissan" in j1):
                for rt in ReleaseScope:
                    if (rt == "aivi2"):   
                        for rs in AIVI2_Type:
                            if (rs == "rnaivi2"):
                                bosch_xml_path = str(bosch_xmlPath) + "\\" + str(rt) + r"\stick" + "\\" + str(rs) + r"\bosch.xml"
            elif ("MMC" in j1):
                for rt in ReleaseScope:
                    if (rt == "aivi2"):   
                        for rs in AIVI2_Type:
                            if (rs == "mmcivi2"):
                                bosch_xml_path = str(bosch_xmlPath) + "\\" + str(rt) + r"\stick" + "\\" + str(rs) + r"\bosch.xml"
            else:
                print ("No Value Found for bosch.xml.")
        
        elif ("P-IVI" in j1):
            for rt in ReleaseScope:
                if (rt == "aivi"):   
                    for rs in AIVI_Type:
                        if (rs == "npivi"):
                            bosch_xml_path = str(bosch_xmlPath) + "\\" + str(rt) + r"\stick" + "\\" + str(rs) + r"\bosch.xml"
        elif ("Renault" in j1):
            for rt in ReleaseScope:
                if (rt == "aivi"):   
                    for rs in AIVI_Type:
                        if (rs == "rivie"):
                            bosch_xml_path = str(bosch_xmlPath) + "\\" + str(rt) + r"\stick" + "\\" + str(rs) + r"\bosch.xml"
        else:
            for rt in ReleaseScope:
                if (rt == "aivi"):   
                    for rs in AIVI_Type:
                        if (rs == "rnaivi"):
                            bosch_xml_path = str(bosch_xmlPath) + "\\" + str(rt) + r"\stick" + "\\" + str(rs) + r"\bosch.xml"
  
        if (str(p1[8][0]).startswith("SplUpd")):
            InputReader.bosch_xml_path = bosch_xml_path.replace("SW_ID", InputReader.Filename_bosch )
            print (InputReader.bosch_xml_path)
        else:
            InputReader.bosch_xml_path = bosch_xml_path.replace("SW_ID", InputReader.Filename)
        
        #print("THe bosch XML path:", InputReader.Filename)

        PD_Path = ConfigPDServerPath
        PDPath = "<a href = Replace >" + PD_Path + "</a>"
        PDPath = PDPath.replace("Replace", PD_Path)

        
        CD_Path = ConfigCDServerPath
        CDPath = "<a href = Replace>" + CD_Path + "</a>"
        CDPath = CDPath.replace("Replace", CD_Path)
        
        V850Path = ServerComPath + "\\"+ "V850\\"
        ADRPath = ServerComPath + "\\" + "ADR3"

        Scope_Names = ["A-IVI2","CCS1.1", "CCS 1.5", "Sc2.1", "Sc3.1", "Sc3.0", "P-IVI2"]
        Scope_Version = ["Scope2.0", "Scope2.1", "Scope3.0", "Scope3.1", "ScopeA2"]
        try: 
            for SN in Scope_Names:
                if (SN in j1):
                    # print(SN)
                    if (SN == "P-IVI2" or SN == "CCS1.1" or SN == "A-IVI2" or SN == "CCS 1.5" ):
                        # print("After the if Inside: SN=", SN)
                        PDPath = PD_Path + "\\" + str(Scope_Version[4]) + "\\" + "PD001" + "\\" 
                        CDPath = CD_Path + "\\" + str(Scope_Version[4]) + "\\" + "CD_DEF" + "\\" 
                        if ("Renault" in j1): 
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file) 
                            break                       
                        elif ("P-IVI" in j1 or "PIVI2" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif ("MMC" in j1 or "P33C" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)   
                        elif ("Nissan" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
            
                elif ("Sc2.1" in j1):
                        PDPath = PD_Path + "\\" + str(Scope_Version[1]) + "\\" + "PD001" + "\\" 
                        CDPath = CD_Path + "\\" + str(Scope_Version[1]) + "\\" + "CD_DEF" + "\\"
                        if ("Renault" in j1): 
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif ("P-IVI" in j1 or "PIVI" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif ("MMC" in j1 or "P33C" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)
                                            
                        elif ("Nissan" in j1):
                        
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                                    
                            for file in list_2:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)
            
            
                elif ("Sc3.0" in j1):
                        PDPath = PD_Path + "\\" + str(Scope_Version[2]) + "\\" + "PD001" + "\\"
                        CDPath = CD_Path + "\\" + str(Scope_Version[2]) + "\\" + "CD_DEF" + "\\"  
                        if ("Renault" in j1): 
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif ("P-IVI" in j1 or "PIVI" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif ("MMC" or "P33C" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)     
                        elif ("Nissan" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
        
                elif (SN == "Sc2.0"):
                        PDPath = PD_Path + "\\" + str(Scope_Version[0]) + "\\" + "PD001" + "\\"
                        CDPath = CD_Path + "\\" + str(Scope_Version[3]) + "\\" + "CD_DEF" + "\\"  
                        if ("Renault" in j1): 
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif ("P-IVI" in j1 or "PIVI" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
            
                        elif ("MMC" in j1 or "P33C" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)  
                        elif ("Nissan" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)             
                elif ("Sc3.1" in j1):
                        PDPath = PD_Path + "\\" + str(Scope_Version[3]) + "\\" + "PD001" + "\\"
                        CDPath = CD_Path + "\\" + str(Scope_Version[3]) + "\\" + "CD_DEF" + "\\"  
                        if ("Renault" in j1): 
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("R-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif ("P-IVI" in j1 or "PIVI" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)            
                        elif  (("MMC" in j1 or "P33C" in j1) and ("ADGE" not in j1 and "AUT" not in j1)):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("M-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)  

                        elif ("Nissan" in j1):
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("N-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)  
                elif ("P-IVI2" in j1 or "PIVI2" in j1):
                    PDPath = PD_Path + "\\" + str(Scope_Version[4]) + "\\" + "PD001" + "\\"
                    CDPath = CD_Path + "\\" + str(Scope_Version[4]) + "\\" + "CD_DEF" + "\\"
                    list_1 = os.listdir(path=PDPath)
                    list_2 = os.listdir(path=CDPath)
                    for file in list_1:
                            if file.startswith("P-") and file.endswith(".odx-e"):
                                if file.endswith(".VarID.odx-e"):
                                    continue
                                else:
                                    PDC = os.path.join(PDPath, file)
                    for file in list_2:
                            if file.startswith("P-") and file.endswith(".odx-e"):
                                if file.endswith(".VarID.odx-e"):
                                    continue
                                else:
                                    CDC = os.path.join(CDPath, file)             
                elif ("P-IVI" in j1):
                            PDPath = PD_Path + "\\" + str(Scope_Version[1]) + "\\" + "PD001" + "\\"
                            CDPath = CD_Path + "\\" + str(Scope_Version[1]) + "\\" + "CD_DEF" + "\\"
                            list_1 = os.listdir(path=PDPath)
                            list_2 = os.listdir(path=CDPath)
                            for file in list_1:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            PDC = os.path.join(PDPath, file)
                            for file in list_2:
                                    if file.startswith("P-") and file.endswith(".odx-e"):
                                        if file.endswith(".VarID.odx-e"):
                                            continue
                                        else:
                                            CDC = os.path.join(CDPath, file)              
                                            
            

                else:
                    #print ("No Scope found, please check")
                    exit
        except UnboundLocalError: 
                print ("Error: PD and CD configs odx-e file might not be available. Please check the inputs.")
                exit()

        InputReader.V850 = "<a href = V850S >" + V850Path  + "</a>"
        InputReader.V850 =  InputReader.V850.replace("V850S", V850Path)

        InputReader.ADR = "<a href = ADRPaths >" + ADRPath + "</a>"
        InputReader.ADR =  InputReader.ADR.replace("ADRPaths", ADRPath)

        Repo_Path = RepoPath
        Repo_input = Repo_Path

        #print(Repo_input)

        InputReader.product = p1[6][0] #input("Please the enter product name Nissan/Renault: ")
        if (str(p1[8][0]) == "SplUpd"):

            base_path = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan"
            servers_location = ["0046","0047","0048", "0049"]
            part_sw1 = []
            #sw_paths = ""
            sw_lnk_name = []
            InputReader.ImagePath = ""

            for index in range(p1[16].count()):
                part_sw1.append(p1[7][index])
            log.info(f"The list of the part sw {part_sw1}")  
            for sw_name in part_sw1:
                for _location in servers_location:
                    sw_path = base_path + "\\" + _location + "_RN_AIVI_7513750800" + "\\00_SW\\_Versions\\" + sw_name + "\\IMX6\\"
                    if (os.path.exists(sw_path) == True):
                        sw_stamp = glob.glob(sw_path+"\\*.lnk")
                        sw_stamp = os.path.basename(str(sw_stamp))
                        sw_stamp = os.path.splitext(sw_stamp)[0]
                        sw_lnk_name.append(sw_stamp)
                        image_resides = base_path + "\\" + _location +"_RN_AIVI_7513750800" + "\\00_SW\\Production\\" +  str(sw_stamp) + "\\Release"
                        if ("TSB" in j1 or "DSB" in j1):
                            if InputReader.product == "Nissan":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                                    ImagePath =  image_resides + r"\_nand_dev\LumenX\rnaivi2"
                                    InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    ImagePath =  image_resides + r"\_nand_dev\LumenX\rnaivi"
                                    InputReader.ImagePath += ImagePath + "\n"

                            elif InputReader.product == "Renault":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                                    if (str(p1[13][0]) == "No" ):
                                        ImagePath =  image_resides + r"\_nand_dev\LumenX\rivie2\WO_PRIVATEKEY"
                                        InputReader.ImagePath += ImagePath + "\n"
                                    else:
                                        ImagePath =  image_resides + r"\_nand_dev\LumenX\rivie2"
                                        InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    if (str(p1[13][0]) == "No" ):
                                        ImagePath =  image_resides + r"\_nand_dev\LumenX\rivie\WO_PRIVATEKEY"
                                        InputReader.ImagePath += ImagePath + "\n"
                                    else:
                                        ImagePath =  image_resides+ r"\_nand_dev\LumenX\rivie"
                                        InputReader.ImagePath += ImagePath + "\n"

                            elif InputReader.product == "P-IVI":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1):
                                    ImagePath =  image_resides + r"\_nand_dev\LumenX\npivi2"
                                    InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    ImagePath =  image_resides + r"\_nand_dev\LumenX\npivi"
                                    InputReader.ImagePath += ImagePath + "\n"
                        
                            elif InputReader.product == "Mitsubishi":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                                    ImagePath =  image_resides + r"\_nand_dev\LumenX\mmcivi2"
                                    InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    ImagePath =  image_resides + r"\_nand_dev\LumenX\rnaivi"
                                    InputReader.ImagePath += ImagePath + "\n"
                                    
                        else:
                            if InputReader.product == "Nissan":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                                    ImagePath =  image_resides + r"\_nand_prd\LumenX\rnaivi2"
                                    InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    ImagePath =  image_resides + r"\_nand_prd\LumenX\rnaivi"
                                    InputReader.ImagePath += ImagePath + "\n"

                            elif InputReader.product == "Renault":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                                    if (str(p1[13][0]) == "No" ):
                                        ImagePath =  image_resides + r"\_nand_prd\LumenX\rivie2\WO_PRIVATEKEY"
                                        InputReader.ImagePath += ImagePath + "\n"
                                    else:
                                        ImagePath = image_resides + r"\_nand_prd\LumenX\rivie2"
                                        InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    if (str(p1[13][0]) == "No" ):
                                        ImagePath = image_resides + r"\_nand_prd\LumenX\rivie\WO_PRIVATEKEY"
                                        InputReader.ImagePath += ImagePath + "\n"
                                    else:
                                        ImagePath = image_resides + r"\_nand_prd\LumenX\rivie"
                                        InputReader.ImagePath += ImagePath + "\n"

                            elif InputReader.product == "P-IVI":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1):
                                    ImagePath = image_resides + r"\_nand_prd\LumenX\npivi2"
                                    InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    ImagePath = image_resides + r"\_nand_prd\LumenX\npivi"
                                    InputReader.ImagePath += ImagePath + "\n"
                            elif InputReader.product == "Mitsubishi":
                                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                                    ImagePath = image_resides + r"\_nand_prd\LumenX\mmcivi2"
                                    InputReader.ImagePath += ImagePath + "\n"
                                else:
                                    ImagePath = image_resides + r"\_nand_prd\LumenX\rnaivi"
                                    InputReader.ImagePath += ImagePath + "\n"
        else:
            if ("TSB" in j1 or "DSB" in j1):
                if InputReader.product == "Nissan":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                        ImagePath =  ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\rnaivi2"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        ImagePath =  ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\rnaivi"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )

                elif InputReader.product == "Renault":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                        if (str(p1[13][0]) == "No" ):
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\rivie2\WO_PRIVATEKEY"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                        else:
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\rivie2"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        if (str(p1[13][0]) == "No" ):
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\rivie\WO_PRIVATEKEY"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                        else:
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\rivie"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )

                elif InputReader.product == "P-IVI":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1):
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\npivi2"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\npivi"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
            
                elif InputReader.product == "Mitsubishi":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\mmcivi2"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_dev\LumenX\rnaivi"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                        
            else:
                if InputReader.product == "Nissan":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                        ImagePath =  ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\rnaivi2"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        ImagePath =  ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\rnaivi"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )

                elif InputReader.product == "Renault":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                        if (str(p1[13][0]) == "No" ):
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\rivie2\WO_PRIVATEKEY"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                        else:
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\rivie2"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        if (str(p1[13][0]) == "No" ):
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\rivie\WO_PRIVATEKEY"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                        else:
                            ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\rivie"
                            InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )

                elif InputReader.product == "P-IVI":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1):
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\npivi2"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\npivi"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                elif InputReader.product == "Mitsubishi":
                    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\mmcivi2"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
                    else:
                        ImagePath = ServerComPath + r"\Production\SW_ID\Release\_nand_prd\LumenX\rnaivi"
                        InputReader.ImagePath = ImagePath.replace("SW_ID", InputReader.Filename )
            
       
        cob = str(p1[10][0])
        #print(cob)
        if (cob == "COB"):
            InputReader.TryOut = "<br> <a href = 'mailto:AIVI.Tryout@de.bosch.com'> @Tryouts Team </a>  – This tryout will be performed @COB </br>" 
        else:
            InputReader.TryOut = " "

        try:
            InputReader.Production_Path
        except:
            print("Error: An error occured. 'Ref - InputReader.Production_Path' ")
            exit()

        try:
            InputReader.imageOverview_Path
        except:
            print("Error: An error occured. 'Ref - InputReader.imageOverview_Path' ")
            exit()

        try:
            InputReader.bosch_xml_path
        except:
            print("Error: An error occured. 'Ref - InputReader.bosch_xml_path' ")
            exit()

        try:
            PDC
            
        except:
            print("Error: An error occured. 'Ref - PDC'. PD Config, odx-e files might not be available. ")
            exit()

        try:
            CDC
        except:
            print("Error: An error occured. 'Ref - CDC'. CD Config, odx-e files might not be available. ")
            exit()
        
        try:
            InputReader.ImagePath, InputReader.V850, InputReader.ADR, Repo_input, InputReader.TryOut
        except:
            print("Error: An error occured. 'InputReader.ImagePath, InputReader.V850, InputReader.ADR, Repo_input, InputReader.TryOut'.")
            exit()

       
            

        return InputReader.Production_Path, InputReader.imageOverview_Path, InputReader.bosch_xml_path, PDC, CDC, InputReader.ImagePath, InputReader.V850, InputReader.ADR, Repo_input, InputReader.TryOut

    def BoschXmlReader():
        mytree = ET.parse(InputReader.bosch_xml_path)
        myroot = mytree.getroot()
        for Bl in myroot.iter('BUILD_LABEL'):
            InputReader.TagName = Bl.text
        for fc in myroot.iter('FINALNAME_CUSTOMER'):
            InputReader.FinalCustomer = fc.text
        for fc in myroot.iter('VERSION'):
            if (fc.text.startswith("rn_") or fc.text.startswith("RN_")):
                InputReader.V850_Ver = fc.text


    
    def ReadIOTtoCSV():
        base_path = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan"
        servers_location = ["0046","0047","0048", "0049"]
        sw_lnk_name = []
        #image_name = []
        part_sw = {}
        emmc_details =[]
        part_details =[]
       # resultCmp = []
        #resultList = []

        for index in range(p1[16].count()):
            part_sw.update({p1[16][index]: p1[7][index]})
        print ("The dictionart of the ds", part_sw)

        if (str(p1[8][0]) == "SplUpd"):  
            for (part_number, sw_name), suc_part in zip (part_sw.items(), p1[0]):
                print(suc_part)
       
                for _location in servers_location:

                    sw_path = base_path + "\\" + _location + "_RN_AIVI_7513750800" + "\\00_SW\\_Versions\\" + sw_name + "\\IMX6\\"
                    if (os.path.exists(sw_path) == True):
                        sw_stamp = glob.glob(sw_path+"\\*.lnk")
                        sw_stamp = os.path.basename(str(sw_stamp))
                        sw_stamp = os.path.splitext(sw_stamp)[0]
                        sw_lnk_name.append(sw_stamp)
                        image_resides = base_path + "\\" + _location +"_RN_AIVI_7513750800" + "\\00_SW\\Production\\" +  str(sw_stamp) + "\\Release\\"
                        if (os.path.exists(image_resides)):
                            image_file = glob.glob(image_resides+"images_overview_" +sw_name[0:4]+ ".txt")
                            #image_name.append(image_file)
                            image_file1 = str(image_file).replace("\\\\", "\\").replace("[","").replace("]", "").replace("'", "")
                            with open(image_file1, "r") as readiot:
                                    readlines_of_iot = readiot.readlines()
                                    count_of_iot = len(readlines_of_iot)
                                    for readeachline in range(count_of_iot):
                                        if (part_number in readlines_of_iot[readeachline] and not "-> use" in readlines_of_iot[readeachline]):
                                            log.info(f"readlines_of_iot[readeachline] - {readlines_of_iot[readeachline].split(':')[0].strip()}")
                                            if (str(readlines_of_iot[readeachline].split(":")[0].strip()) == part_number):
                                                partnumber_line = readlines_of_iot[readeachline]
                                                # print (partnumber_line)
                                                _line_starts_with = partnumber_line.startswith(" ")
                                                # print ("The lines starets: ", _line_starts_with)
                                                split_pn_line = partnumber_line.split(" ")
                                                #file_iot = open("IOT_Test.txt", "w+")
                                                for i in range(len(split_pn_line)):
                                                    if (_line_starts_with == False):
                                                        if (part_number in split_pn_line[i]): 
                                                            pn = split_pn_line[i]
                                                            emmc = split_pn_line[i + 3]
                                                            map_cut = split_pn_line [i + 8]
                                                            map_version = split_pn_line [i + 9].replace(",", "")
                                                            part_details.append(suc_part + "(Pred : " +  pn + ")" + " " + map_cut + " "+ map_version)
                                                            emmc_details.append(pn + " " + emmc)
                                                            
                                    
                                                    else:
                                                        if (part_number in split_pn_line[i]): 
                                                            pn = split_pn_line[i]
                                                            emmc = split_pn_line[i + 1]
                                                            map_cut = split_pn_line [i + 6]
                                                            map_version = split_pn_line [i + 7].replace(",", "")
                                                            part_details.append(suc_part + "(Pred : " +  pn + ")" + " " + map_cut + " "+ map_version)
                                                            emmc_details.append(pn + " " + emmc)
                                            else:
                                                print(f"Info: Input part number {part_number} and the searched part number {str(readlines_of_iot[readeachline].split(':')[0].strip())} in image overview text is not matching")

                                    log.info(f"The Part Details as follows {part_details}")

                                    part_details1 = [re_no_map for re_no_map in part_details if("No_Map ()" not in re_no_map) ]
                                    log.info(f"The Part Details1 as follows {part_details1}")

                            #resultList = part_details1
            return part_details1
                    
        else:
            for part_number, pre_part in zip (p1[0], p1[16]):
                sw_name = str(p1[1][0])
                for _location in servers_location:
                    sw_path = base_path + "\\" + _location + "_RN_AIVI_7513750800" + "\\00_SW\\_Versions\\" + sw_name + "\\IMX6\\"
                    log.info(f"The software path - {sw_path}")
                    if (os.path.exists(sw_path) == True):
                        sw_stamp = glob.glob(sw_path+"\\*.lnk")
                        sw_stamp = os.path.basename(str(sw_stamp))
                        sw_stamp = os.path.splitext(sw_stamp)[0]
                        sw_lnk_name.append(sw_stamp)
                        image_resides = base_path + "\\" + _location +"_RN_AIVI_7513750800" + "\\00_SW\\Production\\" +  str(sw_stamp) + "\\Release\\"
                        if (os.path.exists(image_resides)):
                            image_file = glob.glob(image_resides+"images_overview_" +sw_name[0:4]+ ".txt")
                            #image_name.append(image_file)
                            image_file1 = str(image_file).replace("\\\\", "\\").replace("[","").replace("]", "").replace("'", "")
                    
                            with open(image_file1, "r") as readiot:
                                readlines_of_iot = readiot.readlines()
                                count_of_iot = len(readlines_of_iot)
                                for readeachline in range(count_of_iot):
                                    if (part_number in readlines_of_iot[readeachline] and not "-> use" in readlines_of_iot[readeachline]):
                                        #print("readlines_of_iot[readeachline]", readlines_of_iot[readeachline].split(":")[0].strip())
                                        if (str(readlines_of_iot[readeachline].split(":")[0].strip()) == part_number):
                                            partnumber_line = readlines_of_iot[readeachline]
                                            # print (partnumber_line)
                                            _line_starts_with = partnumber_line.startswith(" ")
                                            # print ("The lines starets: ", _line_starts_with)
                                            split_pn_line = partnumber_line.split(" ")
                                            #file_iot = open("IOT_Test.txt", "w+")
                                            if (_line_starts_with == False):
                                                for sp_pn_line in split_pn_line:
                                                    match = re.search(part_number, sp_pn_line)
                                                    if match:
                                                        pn = sp_pn_line
                                                        p_pn = pre_part
                                                    
                                                    if ("emm" in sp_pn_line):
                                                        emmc = sp_pn_line

                                                    if ("PARTITION_SCHEM" in sp_pn_line):
                                                        map_cut1 = split_pn_line.index(sp_pn_line) + 1
                                                        map_cut = split_pn_line[map_cut1]
                                                        map_version = split_pn_line[map_cut1 + 1]
                                                part_details.append(pn + "(Pred: "+ p_pn + ") " + " " + map_cut + " "+ map_version)
                                                emmc_details.append(pn + " " + emmc) 

                                            else:
                                                for sp_pn_line in split_pn_line:
                                                    match = re.search(part_number, sp_pn_line)
                                                    if match:
                                                        pn = sp_pn_line
                                                        p_pn = pre_part
                                                    
                                                    if ("emm" in sp_pn_line):
                                                        emmc = sp_pn_line

                                                    if ("PARTITION_SCHEM" in sp_pn_line):
                                                        map_cut1 = split_pn_line.index(sp_pn_line) + 1
                                                        map_cut = split_pn_line[map_cut1]
                                                        map_version = split_pn_line[map_cut1 + 1]
                                                part_details.append(pn + "(Pred: "+ p_pn + ") " + " " + map_cut + " "+ map_version)
                                                emmc_details.append(pn + " " + emmc)
                                        else:
                                            print(f"Info: Input part number {part_number} and the searched part number {str(readlines_of_iot[readeachline].split(':')[0].strip())} in image overview text is not matching") 
                            
                                            
                                log.info (f"The Part Details as follows : {part_details}")

                                part_details1 = [re_no_map for re_no_map in part_details if("No_Map ()" not in re_no_map) ]
                                log.info("The part details 1 is as - {part_details1}")
                            #resultList = part_details1
                            print(part_details)
                            
        return part_details1
                
        
    def SU_SWPath():
        base_path = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan"
        servers_location = ["0046","0047","0048", "0049"]
        #sw_lnk_name = []
        #image_name = []
        part_sw1 = []
        #emmc_details =[]
        #part_details =[]
        #resultCmp = []
        sw_paths = ""

        for index in range(p1[16].count()):
            part_sw1.append(p1[7][index])
        #print ("The dictionart of the ds", part_sw1) 

        if (str(p1[8][0]) == "SplUpd"):  
            for sw_name in part_sw1:

                for _location in servers_location:

                    sw_path = base_path + "\\" + _location + "_RN_AIVI_7513750800" + "\\00_SW\\_Versions\\" + sw_name + "\\IMX6\\SW_ID\\Release\\DL\\ai_sw_update"
                    if (os.path.exists(sw_path) == True):
                        sw_paths += sw_path + "\n"
        log.info( f"The software paths as - {sw_paths}")   

        Production_Path1 = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan\0048_RN_AIVI_7513750800\00_SW\_Versions\Sw_Version\_Production"
        InputReader.Production_Path1 = Production_Path1.replace("Sw_Version", str(i1[0]))


        PathF = str(SPF.PathFormation.Prod_RF_Path)
        Ref_Imagepath = str(SPF.PathFormation.RF_BoschXML_Path)

        print("The image path is",  Ref_Imagepath)

        #print ("Ref_Imagepath: ", Ref_Imagepath)

        log.info (f"Path of IMX6:  {PathF}")



        
        #Getting the Shortcut Software timestamp name from the production folder:
        for x in os.listdir(PathF):
            if x.endswith(".lnk") and x.__contains__("_"):
                Filename1 = Path(x).stem

        
        if ("TSB" in j1 or "DSB" in j1):
            if InputReader.product == "Renault":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\rivie2\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\rivie\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)                    

            elif InputReader.product == "Nissan":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1):
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\rnaivi2\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:                        
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\rnaivi\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                
            elif InputReader.product == "P-IVI":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\npivi2\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\npivi\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                
            elif InputReader.product == "Mitsubishi":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\mmcivi2\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\mmcivi\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
            
        else:
            if InputReader.product == "Renault":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\rivie2_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\rivie_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)                    

            elif InputReader.product == "Nissan":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1):
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\rnaivi2_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:                        
                    ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\rnaivi_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                
            elif InputReader.product == "P-IVI":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\npivi2_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\npivi_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                
            elif InputReader.product == "Mitsubishi":
                if ("A-IVI2" in j1 or "CCS1.1" in j1 or "CCS 1.5" in j1):
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi2\stick\mmcivi2_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)
                else:
                    ReflashSWPath = ReflashSWPath = Ref_Imagepath + "\\" + r"aivi\stick\mmcivi_prd_alliance\stick"
                    InputReader.ReflashSWPath = ReflashSWPath.replace("SW_ID",Filename1)

        return InputReader.ReflashSWPath          
           
i1 = InputReader.getInputFromCSV()
i2 = InputReader.inputPath_parser()
i3 = InputReader.BoschXmlReader()
i4 = InputReader.SU_SWPath()
p2 = InputReader.ReadIOTtoCSV()
p3 = InputReader.compare_search_partnumbers()


listPart = tuple(p2)
listI2 =  list(i2)


class mail_content:
    
    def Imagemail_content():
        # HtmlHdr        = { "<HB>" : "<HTML><BODY>",
        #            "<FT>" : "<FONT face=Arial monospaced for SAP size=2>",
        #            "<CT>" : "",
        #            "<HE>" : "<STYLE type=\"text/css\">.cns {font-size: 9pt}</STYLE>",     # Courier New Size between 1 and 2
        #            "<FE>" : "</FONT></FONT></BODY></HTML>",
        #           }
                    # HTML COLOR STYLE ITEM DEFINITION (partly: close old, open new)
        mail_content.HtmlTag        = {
                  "<AS>" : "</FONT><FONT face='Arial' size=2 color=#000000>"           , # Arial Schwarz
                  "<AB>" : "</FONT><FONT face='Arial' size=2 color=#0000ff>"           , # Arial Blue
                   "<AG>": "</FONT><FONT face='Arial' size=2 color=#008000>"           , # Arial Green
                   "<AR>": "</FONT><FONT face='Arial' size=2 color=#ff0000>"           , # Arial Red
                   "<AM>": "</FONT><FONT face='Arial' size=2 color=#c000c0>"            , # Arial Magenta
                   "<CL>": "</FONT><FONT face='Calibri' class=cns color=#000000>" , # Calibri
                   "<CS>": "</FONT><FONT face='Courier New' class=cns color=#000000>"  , # Courier New Schwarz
                   "<CB>": "</FONT><FONT face='Courier New' class=cns color=#0000ff>"  , # Courier New Blue
                   "<CG>": "</FONT><FONT face='Courier New' class=cns color=#008000>"  , # Courier New Green
                   "<CR>": "</FONT><FONT face='Courier New' class=cns color=#ff0000>"  , # Courier New Red
                   "<CM>": "</FONT><FONT face='Courier New' class=cns color=#c000c0>"  , # Courier New Magenta
                   "<SN>": "</STRONG>"                                                 , # Style Normal
                   "<SB>": "<STRONG>"                                                  , # Style Bold
                   "<PB>": "<DIV>"                                                     , # Paragraph Begin
                   "<PE>": "</DIV>"                                                    , # Paragraph End
                   "<TB>": "<PRE>"                                                     , # White Space Preservation Begin
                   "<TE>": "</PRE>"                                                    , # White Space Preservation End
                   "<IB>": "<FONT size=10>&#8226;</FONT>"                              ,#Font SIze to 10
                   "<IF>": "<FONT size=10.5>&#8226;</FONT>"                               , # Bullet
                   "<IL>": "<BR>"                                                      , # Line
                   "<IH>": "-&nbsp;"                                                   , # Hyphen
                   "<IP>": "+&nbsp;"                                                   , # Plus
                   "<IS>": "&nbsp;"                                                    , # Space
                   "<HR>": "<HR>"                                                      , # horizontal Line
                   "<IT>": "&#0009;"                                                   , # Tabulator (needs White Space Preservation)
                   "<LT>": "&#0060;"                                                   , # Less than
                   "<GT>": "&#0062;"                                                   , # Greater than
                   "<LB>": "<A HREF='"                                                 , # Link Begin
                   "<LM>": "'>"                                                        , # Link Middle
                   "<LE>": "</A>"                                                      , # Link End
                  }

        if(str(p1[8][0]) == "Image"):

            mail_content.InitialContent = "<font size = '10px'>" + "Hello All," + "<br> <br> Please perform the Image TryOut " + InputReader.SubTask + " for " + InputReader.MainTask + "<br>" + "<br>  Please reply with TryOut/Checksum Information to this E-Mail. " \
            "<br>  <a href = '@Suriya Thangavel (MS/ECR4-XC)' > @Suriya Thangavel (MS/ECR4-XC) </a>: Please run “NewEntry2Jira.pl” and reply with the results (or problems) to this E-Mail. "\
            "<br> <a href = 'mailto:luong.phamduc@vn.bosch.com'> @Pham Duc Luong (RBVH/ECM22) / <a href = 'mailto:Khang.DoAn@vn.bosch.com'>@Do An KHang (MS/EMC21-XC) <Khang.DoAn@vn.bosch.com> </a>: please confirm the CD/PD in main JIRA task " + InputReader.TryOut + "</font>" + "<br>" +"<br>"

            ChecksumLink = "https://hi-dms.de.bosch.com/docushare/dsweb/View/Collection-"
            cRemoveZero = str(p1[9][0]).replace(".0", "" )
            ChecksumLink = ChecksumLink + cRemoveZero 
        
            ScopeS = re.findall(r'\b\w{2}\d.\d\b', str(j1) )

            if ("P-IVI2" in j1 or "PIVI2" in j1):
                a = "P-IVI2"
            elif ("P-IVI" in j1):
                a = "SC 2.1"                
            elif ("CCS1.1" in j1):
                a = "CCS1.1"
            elif ("A-IVI2" in j1):
                a = "A-IVI2"
            elif ("MMC" in j1 and  "CCS 1.5" in j1 or "CCS1.5" in j1):
                a = "M-IVI2"
            else:
                ScopeS = re.findall(r'\b\w{2}\d.\d\b', str(j1) )
                for i in ScopeS:
                    a = i
            # a = "Check Need to replace"
            mail_content.CheckSumLink = "<b> Checksums Scope " + "<FONT COLOR='RED'>" +  a  + "</FONT>" + " SW  </b> "  + str(p1[1][0])[0:4] + " " +  "<a href >" + ChecksumLink + "</a>"  + "<br>" 

            if ("DSB" in j1 or "TSB" in j1):
                imagesClarification = "<FONT COLOR='RED'> Dev_ Images </b> </FONT>" 
            else:
                imagesClarification = "<FONT COLOR='RED'> Prd_ Images </b> </FONT>"

            mail_content.img_clarification = "<b> Please use the "+ imagesClarification + "<br>"

            
            planned_tentative_date = "DD-MM-YYYY" #now.strftime("%Y-%m-%d %H:%M:%S")
            
            mail_content.ConditionText = "<br> <br> <FONT COLOR='RED'> Work-A-Round for Production required: </FONT> : " + "None / not known" + "<br> <br> <b> Planned Tryout Finished : </b> " +  "<FONT COLOR='RED'>" + planned_tentative_date + "</FONT>" + "<br>"

            mail_content.SW_ID = "<b>" +"SW " +  str(p1[1][0])  + "</b>" +"</br> </br>" 
            
            mail_content.ConfigContent= "<br>" "<br>"+ "<br>" + mail_content.HtmlTag['<CS>'] +  "PD Configuration"   + "</br>" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + ":"  + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + str(p1[4][0]) + "<br>"+ str(i2[3]) + "<br>" + "<br>" + "<br>" + mail_content.HtmlTag['<CS>'] + "CD Configuration" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + ":"  + mail_content.HtmlTag['<IS>']  + mail_content.HtmlTag['<IS>']+ str(p1[5][0]) + "<br>" + str(i2[4]) + "<br>" "<br>"

            mail_content.MAPheading = "MAPs:"

            return mail_content.InitialContent, mail_content.ConfigContent, mail_content.MAPheading
       
        elif(str(p1[8][0]) == "SplUpd"):

            mail_content.InitialContent = "<font size = '10px'>" + "Hello All," + "<br> <br> Please perform the Special Update TryOut " + InputReader.SubTask + " for " + InputReader.MainTask + "<br>"  + "<br>  Please reply with TryOut/Checksum Information to this E-Mail."\
            "<br>  <a href = 'mailto:thangavel.suriya@in.bosch.com' > @Suriya Thangavel (MS/ECR4-XC) </a>: Please run “NewEntry2Jira.pl” and reply with the results (or problems) to this E-Mail."\
            "<br>  <a href = 'mailto:Markus.Kraemer2@de.bosch.com' > @Kraemer Markus (XC-CP/ERN7-E) </a>: <b>:- Finding in compatibility matrix:</b> "\
             "<br> <a href = 'mailto:luong.phamduc@vn.bosch.com'> @Pham Duc Luong (RBVH/ECM22) / <a href = 'mailto:Khang.DoAn@vn.bosch.com'>@Do An KHang (MS/EMC21-XC) <Khang.DoAn@vn.bosch.com> </a>: please confirm the CD/PD in main JIRA task" + InputReader.TryOut +  "</font>" + "<br>" + "<br>"

            ChecksumLink = "https://hi-dms.de.bosch.com/docushare/dsweb/View/Collection-"
            cRemoveZero = str(p1[9][0]).replace(".0", "" )
            ChecksumLink = ChecksumLink + cRemoveZero
           
            if ("P-IVI2" in j1 or "PIVI2" in j1):
                _scope = "P-IVI2"
            elif ("P-IVI" in j1):
                _scope = "SC 2.1"                
            elif ("CCS1.1" in j1):
                _scope = "CCS1.1"
            elif ("A-IVI2" in j1):
                _scope = "A-IVI2"
            elif ("MMC" in j1 and "CCS 1.5" in j1):
                _scope = "M-IVI2"
            else:
                ScopeS = re.findall(r'\b\w{2}\d.\d\b', str(j1) )
                for i in ScopeS:
                    _scope = i

            mail_content.CheckSumLink = "<b> Checksums Scope " + "<FONT COLOR='RED'>" +  _scope  + "</FONT>" + " SW  </b> "  + "<b>" + str(p1[1][0])[0:4] + "</b>" + " " +  "<a href >" + ChecksumLink + "</a>"  + "<br>" 

            
            if ("DSB" in j1 or "TSB" in j1):
                imagesClarification = "<FONT COLOR='RED'> Dev_ Stick </b> </FONT>" 
            else:
                imagesClarification = "<FONT COLOR='RED'> Prd_Alliance_stick </b> </FONT>"

            mail_content.img_clarification = "<b> Please use the "+ imagesClarification + "<br>"

            #now = datetime.datetime.now()

            planned_tentative_date = "DD-MM-YYYY"
            
            mail_content.ConditionText = "<br> <br> <FONT COLOR='RED'> Work-A-Round for Production required: </FONT> : " + "None / not known" + "<br> <br> <b> Planned Tryout Finished : </b> " +  "<FONT COLOR='RED'>" + planned_tentative_date + "</FONT>" + "<br>"

 
            mail_content.SW_ID = "<b>" +"SW " +  str(p1[1][0])  + "</b>" +"</br> </br>" 
            mail_content.SW_RF = "<b>" +"SW " + str(p1[7][0])  + "</b>" +"</br> </br>"
            
            mail_content.ConfigContent= "<br>" "<br>"+ "<br>" + mail_content.HtmlTag['<CS>'] +  "PD Configuration"   + "</br>" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] +  mail_content.HtmlTag['<IS>'] +  ":"  + mail_content.HtmlTag['<IS>']  + mail_content.HtmlTag['<IS>']+ str(p1[4][0]) + "<br>"+ str(i2[3]) + "<br>" + "<br>"  + "<br>" + mail_content.HtmlTag['<CS>'] +"CD Configuration" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + ":"  + mail_content.HtmlTag['<IS>']  + mail_content.HtmlTag['<IS>']+ str(p1[5][0]) + "<br>" + str(i2[4]) + "<br>" "<br>"

            mail_content.MAPheading = "MAPs:"
            
            return mail_content.InitialContent, mail_content.ConfigContent,mail_content.MAPheading


mail_content.Imagemail_content()

def repository_Collector():
    if (str(p1[8][0]) == "SplUpd" or "Special Update"):
        Repo_Path = SPF.PathFormation.Repo_ReflashPath
    else:
        Repo_Path = SPF.PathFormation.Repo_Path
        
    Repo_input = str(Repo_Path)

    repository_Collector.BaseValues={}
    repository_file = open(Repo_input)
    read_repo = repository_file.readlines()
    for lines in read_repo:
        SearchbyValue = re.search("^(_\\w+.*)", lines)
        if SearchbyValue !=None:
            grpDict = SearchbyValue.group(0)
            # key, value = grp.split('=')
            # a_dictionary[key] = value
            SplitDict=grpDict.split('=') 
            repository_Collector.BaseValues[SplitDict[0]]=SplitDict[1]

    repository_Collector.mydict = {             
                        'RFS GEN3'                        : '_PF_BASE_VERSION',
                        'RFS GEN4'                        : '_PF_G4_BASE_VERSION',
                        'NDS Navigation'                  : '_NaviSDK_VERSION',
                        'NDS Navi PIVI'                   : '_NaviSDK_JP_PIVI_VERSION',
                        'NDS Navi Korea'                  : '_NaviSDK_KOREA_VERSION',
                        'NDS Navi Japan'                  : '_NaviSDK_JP_VERSION',
                        'RCAR_R7 (A-IVI2/P-IVI3.1'        : '_AUTOSAR_VERSION_GEN4_RCAR_R7',
                        'STA8088'                         : '_TESEO_VERSION_STA8088',
                        'STA8089'                         : '_TESEO_VERSION_STA8089',
                        'ADR (S0_NA_HD)'                  : '_AARS_IVI_S0_NA_HD_VERSION',
                        'ADR (S0_NA_DAB)'                 : '_AARS_IVI_S0_NA_DAB_VERSION',
                        'ADR (S1_NA_FM)'                  : '_AARS_IVI_S1_NA_FM_VERSION',
                        'ADR (S2_AC_HD)'                  : '_AARS_IVI_S2_AC_HD_VERSION',
                        'ADR (S2_AC_FMSD)'                : '_AARS_IVI_S2_AC_FMSD_VERSION',
                        'ADR (S2_AC_FM)'                  : '_AARS_IVI_S2_AC_FM_VERSION',
                        'ADR (S2_AC_DRM)'                 : '_AARS_IVI_S2_AC_DRM_VERSION',
                        'ADR (S2_AC_DARC)'                : '_AARS_IVI_S2_AC_DARC_VERSION',
                        'ADR (S2_AC_DAB)'                 : '_AARS_IVI_S2_AC_DAB_VERSION',
                        'ADR (A2_P1_DAB)'                 : '_AARS_IVI_A2_P1_DAB_VERSION',
                        'ADR (A2_P1_DARC)'                : '_AARS_IVI_A2_P1_DARC_VERSION',
                        'ADR (A2_P1_FM)'                  : '_AARS_IVI_A2_P1_FM_VERSION',
                        'ADR (A2_P1_HD)'                  : '_AARS_IVI_A2_P1_HD_VERSION',
                        'v850 Testmanager'                : '_TM_V850_VERSION',
                        'iMX Testmanager'                 : '_TM_IMX_VERSION',
                        'V850 (PIVI)'                     : '_AUTOSAR_VERSION_RNPIVI',
                        'V850 (SCOPE2.x)'                 : '_AUTOSAR_VERSION_RNAIVI',   
                        'SBR Version'                     : '_SBR_VERSION',

    }
   
    return repository_Collector.mydict


dict1 = repository_Collector()


def mail_generator():

    if ("A-IVI2" in j1 or "CCS1.1" in j1 or "MMC" in j1 and "CCS 1.5" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1 or "PIVI2" in j1):
        SubjectLine =  "[RN_AIVI2][TryOut] Image TryOut for " + str(p1[15][0]) + " - SW " + str(p1[1][0])
        SubjectLineSpdUpd = "[RN_AIVI2][TryOut] Special Update TryOut for " + str(p1[15][0]) + " - SW " + str(p1[1][0])
    else:
        SubjectLine = "[RN_AIVI][TryOut] Image TryOut for " + str(p1[15][0])  + " - SW " + str(p1[1][0])
        SubjectLineSpdUpd = "[RN_AIVI][TryOut] Special Update TryOut for " + str(p1[15][0]) + " - SW " + str(p1[1][0])
    
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

    
    if ( str(p1[8][0]) == "Image"):

        olApp = win32.Dispatch('Outlook.Application')
       # olNS = olApp.GetNameSpace("MAPI")
        mail = olApp.CreateItem(0)
        mail.Subject = SubjectLine
        mail.BodyFormat = 1
        mail.HTMLBody = mail_content.InitialContent + mail_content.CheckSumLink +'<a href >' + "<br>" + InputReader.ImagePath + '</a>' + "<br>" + '<a href >' + InputReader.imageOverview_Path + '</a>' + "<br>" + "<br>"+ mail_content.img_clarification + "<br>"+ "<b>" + mail_content.MAPheading + "</b>" \
        + "<br>"\
        + "<br>"
       
        if not p2:
            mail.HTMLBody += "No Maps"
            mail.HTMLBody += "<br>"
        else:
            for partnumber_mapName in p2:
                print("p2. -> ", partnumber_mapName )
                
                replace_partnumber_mapName = str(partnumber_mapName).replace(",", "").replace("'", "")
                mail.HTMLBody += str(replace_partnumber_mapName).lstrip('(')
                mail.HTMLBody += "<br>"

        
        mail.HTMLBody += mail_content.ConditionText  + "<br>"
        #Below Code if find the Sister Device:
        mail.HTMLBody+= "<b>"+ "TryOut Devices:" +"</b>"\
        + "<br>"\
        + "<IS>" \
        + "<br>"     
        if(NeedToRun == "y" or NeedToRun == "Y"):
            mail.HTMLBody+= "<br>"            
            PartNumbers = p1[0]
            Pre_PartNumbers = p1[16]

            for part, part1 in zip (PartNumbers, Pre_PartNumbers):
                # pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-p" , part])
                pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-hwlist", p1[12][0], "-p" , part])

                Byte_To_String = str(pipe)

                ValueOfDevice = re.findall('\\|\\^\\_([^"]*)\\_\\^\\|', Byte_To_String)
                mail.HTMLBody+=  "<b>" + str(part) + "( Pred: " + (str(part1)) + ")" +"</b>" + ":" + str(ValueOfDevice)
                mail.HTMLBody+= "<br>"
        elif(NeedToRun == "n" or NeedToRun == "N"):
            print ("\n Info: Mail will be generated without sister device. Please add the Sister Device.")
            mail.HTMLBody+= "No to Sister Devices, please add the sister device."
            #Upto this, the above Code finds the Sister Device:    
        if ("A-IVI2" in j1 or "CCS1.1" in j1 or "MMC" in j1 and "CCS 1.5" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1 or "PIVI2" in j1):
            mail.HTMLBody+= "<br>"
            mail.HTMLBody+= "<b>"+ "Note: " +"</b>"
            mail.HTMLBody+= "BoardID – Hyperflash file name assignment for the release to production"\
            + "<br>"\
            + "<br>"  
         
            PartNumbers = p1[0]
            Pre_PartNumbers = p1[16]
            

            for part, part1 in zip (PartNumbers, Pre_PartNumbers):
                # pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-p" , part])
                pipe1 = subprocess.check_output(["perl", r"Fetch_from_FCID.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-p" , part])
                Byte_To_String = str(pipe1)
                _boardID = re.search('Board_ID.+\\(', Byte_To_String)
                mail.HTMLBody+=  f"<b>{_boardID.group(0).split('=')[1].replace('(','')}</b> : {hyper_flash[_boardID.group(0).split('=')[1].replace(' ', '').replace('(', '')][1]} "
                mail.HTMLBody+= "<br>"
                 
        else:
            mail.HTMLBody+= ""
            
        mail.HTMLBody+= "<br>"
     
        mail.HTMLBody+= "<br>" + mail_content.SW_ID + "<br>"\
        + mail_content.HtmlTag['<CS>'] + "Used for " + str(InputReader.MainTask).replace (str(j1), str(str(p1[15][0]))) +  "<br>" + "<br>"\
        + mail_content.HtmlTag['<CS>'] + "<br>" + 'SW-ID' + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"] +mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"]+":"+mail_content.HtmlTag["<IS>"] + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"] +InputReader.FinalCustomer + "<br>" \
        + mail_content.HtmlTag['<CS>'] + 'TAG' + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"] +mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"]+ ":" + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"]+ mail_content.HtmlTag["<IS>"] + InputReader.TagName + "<br>"\
        + "<br>" + '<a href >' + InputReader.ImagePath + '</a>' + "<br>" + '<a href >' + InputReader.imageOverview_Path + '</a>' + "<br>" \
        
        mail.HTMLBody+= "<br>"
        
        mail_generator.list1 = []

        for i in dict1.keys():
            if dict1[i] in repository_Collector.BaseValues.keys():
                if "AARS" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] = "AARS_IVI_" + repository_Collector.BaseValues[dict1[i]]
                    mail_generator.list1.append(repository_Collector.BaseValues[dict1[i]])
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"


                if "_TM_V850" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] = repository_Collector.BaseValues[dict1[i]]
            

                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_TM_IMX" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_STA8088" in dict1[i]:

                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
     
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_STA8089" in dict1[i]:                  
                    repository_Collector.BaseValues[dict1[i]] = repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"  

                if "_NaviSDK_VERSION" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"
                if "_NaviSDK_JP_VERSION" in dict1[i]:
                    
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_SBR_VERSION" in dict1[i]:
                    
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"                
                
                if ("A-IVI2" in j1):
                    if "_PF_G4_BASE_VERSION" in dict1[i]:
                        repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                
                        mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"  
            else:
                print (f"\n \t \033[93m Warning : \033[00m The {dict1[i]} is not found in the repository file. Please add manually.\n")
                log.info (f"\n \t Warning: The {dict1[i]} is not found in the repository file. Please add manually.")                              
        if ("P-IVI2" in j1 or "PIVI2" in j1):
            scope_nm = "P-IVI2"
        elif ("P-IVI" in j1):
            scope_nm = "SC 2.1"
        elif ("CCS1.1" in j1):
            scope_nm = "CCS1.1"
        elif ("A-IVI2" in j1):
            scope_nm = "A-IVI2"
        elif ("MMC" in j1 and "CCS 1.5" in j1 or "CCS 1.5" in j1):
            scope_nm = "M-IVI2"                   

        if ("A-IVI2" in j1 or "CCS1.1" in j1 or "MMC" in j1 and "CCS 1.5" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1):
            mail.HTMLBody+= "<br>" + "<br>" + InputReader.ADR  +"<br>" + "<b>" + "<br>" + str(p1[6][0])+ "("+ scope_nm +")" + "</b>" +  mail_content.ConfigContent
            print ("\n Info: The mail will be generated and displayed in the new compose window")
            log.info ("\n Info: The mail will be generated and displayed in the new compose window")
        else:
            mail.HTMLBody+= "<br>" + "<b> V850 </b>" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + ":" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + InputReader.V850_Ver  + "<br>" + InputReader.V850 + "<br>" +"<br>" + InputReader.ADR + "<br>" + "<br>" + "<b>" + str(p1[6][0]) + "</b>" + "<br>" +  mail_content.ConfigContent
            print ("\n Info: The mail will be generated and displayed in the new compose window")
            log.info ("\n Info: The mail will be generated and displayed in the new compose window")


        

        OlSaveAsType = {
                            "olTXT": 0,
                            "olRTF": 1,
                            "olTemplate": 2,
                            "olMSG": 3,
                            "olDoc": 4,
                            "olHTML": 5,
                            "olVCard": 6,
                            "olVCal": 7,
                            "olICal": 8
                        }
        
     
        mail.SaveAs(os.getcwd()+'//'+str(p1[1][0])+".txt", OlSaveAsType['olTXT'])

        mail_generator.callMail = mail


    elif(str(p1[8][0]) == "SplUpd" or "Special Update"):
        olApp = win32.Dispatch('Outlook.Application')
        #olNS = olApp.GetNameSpace("MAPI")
        mail = olApp.CreateItem(0)
        mail.Subject = SubjectLineSpdUpd
        mail.BodyFormat = 1
        
        #Removing Duplicates in imagesoverview path
        lines_list = InputReader.imageOverview_Path.strip().split('\n')
        unique_lines = set(lines_list)
        InputReader.imageOverview_Path = '\n'.join(unique_lines)
        #Removing Duplicates
        lines_list1 = InputReader.ImagePath.strip().split('\n')
        unique_lines1 = set(lines_list1)
        InputReader.ImagePath = '\n'.join(unique_lines1)

        print ( str(p3[2])) 
        if (p3[2] > 0):
            InputReader.ReflashSWPath = "<< Please update the Stick Manually >>"
        
        mail.HTMLBody = mail_content.InitialContent + mail_content.CheckSumLink  + "<br>" + '<a href >' + InputReader.ReflashSWPath + '</a>' + "<br>"  + "<br>"+ mail_content.img_clarification + "<br>"+ "<b>" + mail_content.MAPheading + "</b>" \
        + "<br>"\
        + "<br>"

        if not p2:
            mail.HTMLBody += "No Maps"
            mail.HTMLBody += "<br>"
        else:

            for rcm in p2:
                b = str(rcm).replace(",", "").replace("'", "")
                mail.HTMLBody += str(b).lstrip('(')
                mail.HTMLBody += "<br>"        


        mail.HTMLBody +=  mail_content.ConditionText  + "<br>"

        mail.HTMLBody +=  "<br>"
        #Below Code if find the Sister Device:
        mail.HTMLBody+= "<b>"+ "TryOut Devices:" +"</b>"\
        + "<br>"\
        + "<IS>" \
        + "<br>"\
        + "<br>"
        if (NeedToRun == "Y" or NeedToRun == "y"):
            mail.HTMLBody+= "<br>"            
            PartNumbers = p1[16]
            Pre_PartNumbers = p1[0]

            for part,part1 in zip(PartNumbers,Pre_PartNumbers):
                #pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-p" , part])

                pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-hwlist", p1[12][0], "-p" , part])
    
                Byte_To_String = str(pipe)

                ValueOfDevice = re.findall('\\|\\^\\_([^"]*)\\_\\^\\|', Byte_To_String)
                mail.HTMLBody+=  "<b>" + str(part) + "( Pred: " + str(part1) + ")" +"</b>" + ":" + str(ValueOfDevice)
                mail.HTMLBody+= "<br>"
        elif(NeedToRun == "N" or NeedToRun == "n"):
            print ("**** This mail will be generated without Sister Device. ****")
            log.info ("**** This mail will be generated without Sister Device. ****")
            mail.HTMLBody+= "No to Sister Devices, please add the sister device."
            
        #Upto this, the above Code finds the Sister Device:
        '''
        print ("The list that contains ", p1[7], len(p1[7]))
        base_counter = 0
        for base_count in p1[7]:
            if  (p3[2] >= 1 or p3[3] >= 1):
                if (p3[0][base_counter] == "No_Map" and "7.50" in p1[0][base_counter]):
                    mail.HTMLBody+= "<br>  <FONT COLOR='RED'> Device preparation: </FONT> SW "  + str(base_count) + " See " + "<a href = " + jira_url_browse + str(p1[17][base_counter])  + ">" + str(p1[17][base_counter]) +  "</a>"  + " -> Config update for SW "+ str(p1[1][0]).split("_")[0] + "-> " + " Stick update " + "( " + "SW " + str(p1[1][0]).split("_")[0] +" )" + "<br>"
                else:
                    mail.HTMLBody+= "<br>  <FONT COLOR='RED'> Device preparation: </FONT> SW "  + str(base_count) + " See " + "<a href = " + jira_url_browse + str(p1[17][base_counter])  + ">" + str(p1[17][base_counter]) +  "</a>"  + " -> Config update for SW "+ str(p1[1][0]).split("_")[0] + "-> " + " Stick update " + "( " + "SW " + str(p1[1][0]).split("_")[0] +" )" + " ->  WA to remove the existing MAP " + "(" + str(p3[0]) +  ")"  + " -> "+ "Map Update " + "(" +  str( p3[1]) +")" + "<br>"
            else:
                mail.HTMLBody+= "<br>  <FONT COLOR='RED'> Device preparation: </FONT> SW "  + str(base_count) + " See " + "<a href = " + jira_url_browse + str(p1[17][base_counter])  + ">" + str(p1[17][base_counter]) +  "</a>" + "<br>"
            base_counter  = base_counter + 1 '''

        mail.HTMLBody += p3[4]
        mail.HTMLBody+= "<br>"  
        if ("A-IVI2" in j1 or "CCS1.1" in j1 or "MMC" in j1 and "CCS 1.5" in j1 or "CCS 1.5" in j1 or "P-IVI2" in j1 or "PIVI2" in j1):
            mail.HTMLBody+= "<br>"
            mail.HTMLBody+= "<b>"+ "Note: " +"</b>"
            mail.HTMLBody+= "BoardID – Hyperflash file name assignment for the release to production"\
            + "<br>"\
            + "<br>"             
            
            PartNumbers = p1[16]
            Pre_PartNumbers = p1[1]

            for part,part1 in zip(PartNumbers,Pre_PartNumbers):
                # pipe = subprocess.check_output(["perl", r"tryout_devices.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-p" , part])
                pipe1 = subprocess.check_output(["perl", r"Fetch_from_FCID.pl", "-fcid", 'SWUPD_Tooling_'+ p1[11][0] +'.xlsx', "-p" , part])
                Byte_To_String = str(pipe1)
                _boardID = re.search('Board_ID.+\\(', Byte_To_String)
                mail.HTMLBody+=  f"<b>{_boardID.group(0).split('=')[1].replace('(', '')}</b> : {hyper_flash[_boardID.group(0).split('=')[1].replace(' ', '').replace('(', '')][1]}," + part+"("+ "Pred: " + part1 + ")" 
                mail.HTMLBody+= "<br>"
        else:
            mail.HTMLBody+= ""
            
        mail.HTMLBody+= "<br>"
        
        mail.HTMLBody+= "<br>" + mail_content.SW_ID + "<br>"\
        + mail_content.HtmlTag['<CS>'] + "Used for " +  str(InputReader.MainTask).replace (str(j1), str(str(p1[15][0]))) + "<br>"\
        + mail_content.HtmlTag['<CS>'] + "<br>" + 'SW-ID' + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"] +mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"]+":"+mail_content.HtmlTag["<IS>"] + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"] +InputReader.FinalCustomer + "<br>" \
        + mail_content.HtmlTag['<CS>'] + 'TAG' + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"] +mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"]+ ":" + mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"]+mail_content.HtmlTag["<IS>"] + InputReader.TagName + "<br>"\
        + "<br>" + '<a href >' + InputReader.ImagePath + '</a>' + "<br>" + '<a href >' + InputReader.imageOverview_Path + '</a>' + "<br>" \
        + "<br>" "<br>"
               
        mail_generator.list1 = []

        for i in dict1.keys():
            if dict1[i] in repository_Collector.BaseValues.keys():
                if "AARS" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] = "AARS_IVI_" + repository_Collector.BaseValues[dict1[i]]
                    mail_generator.list1.append(repository_Collector.BaseValues[dict1[i]])
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_TM_V850" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_TM_IMX" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_STA8088" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"

                if "_STA8089" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>" 

                if "_NaviSDK_VERSION" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"
                    
                if "_NaviSDK_JP_VERSION" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"
            
                if "_SBR_VERSION" in dict1[i]:
                    repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                    mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"


                if ("A-IVI2" in j1):
                    if "_PF_G4_BASE_VERSION" in dict1[i]:
                        repository_Collector.BaseValues[dict1[i]] =  repository_Collector.BaseValues[dict1[i]]
                        mail.HTMLBody +=  mail_content.HtmlTag['<CS>'] + i  +  mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ "  :  "+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+ mail_content.HtmlTag['<IS>']+  mail_content.HtmlTag['<CS>'] + repository_Collector.BaseValues[repository_Collector.mydict[i]] +"<br>"
            else:
                print (f"\033[93m Warning : \033[00m The {dict1[i]} is not found in the repository file. Please add manually. \n")
                log.info (f"Warning: The {dict1[i]} is not found in the repository file. Please add manually.\n")             
                   
        if ("P-IVI2" in j1 or "PIVI2" in j1):
            scope_nm = "P-IVI2"
        elif ("P-IVI" in j1):
            scope_nm = "SC 2.1"            
        elif ("CCS1.1" in j1):
            scope_nm = "CCS1.1"
        elif ("A-IVI2" in j1):
            
            scope_nm = "A-IVI2"
        elif ("MMC" in j1 and "CCS 1.5" or "CCS1.5" in j1):
            scope_nm = "M-IVI2"                   

        if ("A-IVI2" in j1 or "CCS1.1" in j1 or "P-IVI2" in j1 or "MMC" in j1 and "CCS 1.5" in j1):
            mail.HTMLBody+= "<br>" + "<br>" + InputReader.ADR  +"<br>" + "<br>" + "<b>" + str(p1[6][0])+ "("+ scope_nm +")" + "</b>" +  mail_content.ConfigContent
            print ("The mail will be generated, Please see the Mail compose window")
            log.info ("The mail will be generated, Please see the Mail compose window")
        else:
            mail.HTMLBody+= "<br>" + "<b> V850 </b>" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + ":" + mail_content.HtmlTag['<IS>'] + mail_content.HtmlTag['<IS>'] + InputReader.V850_Ver  + "<br>" + "<br>" + InputReader.V850 + "<br>" + "<br>" + "<br>" + InputReader.ADR  +"<br>" + "<br>"+ "<b>" + str(p1[6][0]) + "</b>" + "<br>" + mail_content.ConfigContent
            print ("The mail will be generated, Please see the Mail compose window")
            log.info ("The mail will be generated, Please see the Mail compose window")
    
    
   
   
    OlSaveAsType = {
                        "olTXT": 0,
                        "olRTF": 1,
                        "olTemplate": 2,
                        "olMSG": 3,
                        "olDoc": 4,
                        "olHTML": 5,
                        "olVCard": 6,
                        "olVCal": 7,
                        "olICal": 8
                    }
     
    mail.SaveAs(os.getcwd()+'//'+ str(p1[1][0])+".txt", OlSaveAsType['olTXT'])

    mail_generator.callMail = mail
        
    # mail.Display()  



mail_generator()


if(p3[2] >= 1 ): 
    warn_part = f"\n {LightBlue}***  Notification *** : Successor and Predecessor part numbers are not in the same FCID row.{RESET}"
else:
    warn_part = ""
    
if (p3[3] >= 1):
    warn_map = f"\n {LightBlue}***  Notification *** : MAP for Successor and Predecessor part numbers are not in the same FCID table.{RESET}"
else:
    warn_map = ""

#This below part of the Code is for Copy Binaries:

Want_To_Copy = AskToCopy

Want_To_Copy = Want_To_Copy.strip().lower()

if (Want_To_Copy == "Y" or Want_To_Copy == "y"):

    def copy_binaries():
        ADR3 = mail_generator.list1


        for i in ADR3:
            Source_path = r"//bosch.com/dfsrb/DfsDE/DIV/CM/AI/SW_Releases/Nissan/0048_RN_AIVI_7513750800/00_SW/ADR3/"
            Dest_Path  = r"\\cob0fs03.apac.bosch.com\TRY1COB$\Tryout\ADR"
            try:
                source = os.path.join(Source_path, i)
                destination = os.path.join(Dest_Path, i)
                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                    print(f"Folder '{i}' copied successfully.")
                elif os.path.isfile(source):
                    shutil.copy2(source, destination)
                    print(f"File '{i}' copied successfully.")
                #else:
                    #print(f"File or folder '{name}' not found in the source path '{source}'.")
            except FileExistsError:
                print(f"File or folder '{i}' already exists in the destination path '{destination}'.")
            except Exception as e:
                print(f"An error occurred while copying file or folder '{i}': {e}")
        #V850: Copy
        V850 =  InputReader.V850_Ver

        V850S = V850.replace("rn_aivi", "RN_AIVI").replace("ar", "AUTOSAR").replace("_stabi_", "S")
        Server = ["0046", "0047", "0048", "0049"]
        for i in Server:
            Source_path = r"//bosch.com/dfsrb/DfsDE/DIV/CM/AI/SW_Releases/Nissan/" + i + "_RN_AIVI_7513750800/00_SW/V850/" + V850S
            if (os.path.exists(Source_path)):
                source = Source_path
                print ("it exists in the ", source)
        source = source

        Dest_Path  = r"\\cob0fs03.apac.bosch.com\TRY1COB$\Tryout\V850"
        destination = os.path.join(Dest_Path, V850S)
        try:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
                print(f"Folder '{V850S}' copied successfully.")
            elif os.path.isfile(source):
                shutil.copy2(source, destination)
                print(f"File '{V850S}' copied successfully.")
            #else:
                #print(f"File or folder '{name}' not found in the source path '{source}'.")
        except FileExistsError:
            print(f"File or folder '{V850S}' already exists in the destination path '{destination}'.")
        except Exception as e:
            print(f"An error occurred while copying file or folder '{V850S}': {e}")

    #PD and CD: Copy

        Source_path_pd = str(i2[3])
        Source_path_cd = str(i2[4])
        Dest_Path_pd  = r"\\cob0fs03.apac.bosch.com\TRY1COB$\Tryout\PD"
        Dest_Path_cd  = r"\\cob0fs03.apac.bosch.com\TRY1COB$\Tryout\CD"

        dest_pd = os.path.join(Dest_Path_pd, str(p1[4][0]))
        dest_cd = os.path.join(Dest_Path_cd, str(p1[5][0]) )

        Src_list_pd  = Source_path_pd.split("\\")
        Src_list_cd  = Source_path_cd.split("\\")

        des_file = os.path.join(dest_pd, str(Src_list_pd[-1]))
        des_file1 = os.path.join(dest_pd, str(Src_list_cd[-1]))
        try:
            if os.path.isfile(Source_path_pd):
                if os.path.exists(dest_pd):
                    if os.path.exists(des_file):
                        print ("The file is already exists.")
                    else:
                        shutil.copy2(Source_path_pd, dest_pd)
                        print("File copied successfully.")
                else:
                    os.chdir(Dest_Path_pd)
                    os.mkdir(str(p1[4][0]))
                    shutil.copy2(Source_path_pd, dest_pd)
                    print(f"File {str(Src_list_pd[-1])} copied successfullys.")
            #else:
            #   print(f"File or folder '{name}' not found in the source path '{source}'.")
        except FileExistsError:
            print(f"File or folder already exists in the destination path '{dest_pd}'.")
        except Exception as e:
            print("An error occurred while copying file or folder")

        #cd_Cop
        try:
            if os.path.isfile(Source_path_cd):
                if os.path.exists(dest_cd):
                    if os.path.exists(des_file1):
                        print ("The file is already exists.")
                    else:
                        shutil.copy2(Source_path_cd, dest_cd)
                        print("File copied successfully.")
                else:
                    os.chdir(Dest_Path_cd)
                    os.mkdir(str(p1[5][0]))
                    shutil.copy2(Source_path_cd, dest_cd)
                    print("File copied successfullys.")
            #else:
            #   print(f"File or folder '{name}' not found in the source path '{source}'.")
        except FileExistsError:
            print(f"File or folder already exists in the destination path '{dest_cd}'.")
        except Exception as e:
            print("An error occurred while copying file or folder")
    copy_binaries()
elif (Want_To_Copy == "N" or Want_To_Copy == "n"):
    print ("\n Info: Please copy the binaries manually, if you needed ")
else:
    print (f"You have to enter only Y for (Yes) and N for (No) whether the copy the binaries, but you have entered : {Want_To_Copy}")

if __name__ == "__main__":
   print("\n Info: *** Updating the Jira is started ***")
   main_obj=Jira_issue_create()
   main_obj.readCSV_InputFile()
   main_obj.set_inputs()
   #main_obj.get_inputs()
   main_obj.extract_description()
   main_obj.read_tryoutMail()
   main_obj.read_image_overview()
   main_obj.getData_Jira()
   #main_obj.destroy_txtfile()
   mail_generator.callMail.Display()
   print (warn_map)
   print (warn_part)
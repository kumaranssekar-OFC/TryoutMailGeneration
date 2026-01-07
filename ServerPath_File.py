"""
Crafting with Care

started on 02-05-2024 @ 13:24 

By Creator: Kumaran Sekar (MS\ECR4-XC); (EUJ1COB);

Changes:
27-11-2024  : Comments added.

"""

import datetime
from tkinter import Image
import pandas as pd
import os 
import warnings

class PathFormation:
    
    print ("Start Time: ", datetime.datetime.now())
    
    BasePath = r'\\bosch.com\dfsrb\dfsde\DIV\CM\AI\SW_Releases\Nissan'
    ServerStart  = 46
    ServerEnd = 49

    warnings.filterwarnings("ignore")

    print (

"""
    \033[92m
            +----------------------+
            |Tryout mail generator |
            |        **  ** * *    |
            | * *   *  *   * *  ** |
            |* * **            *   |
            |        *        *    |
            |                      |
            |*    *    *       *   |
            |    *  *              |
            |             ***      |
            |   *               *  |
            |            *         |
            |  *                   |
            | *       *      *   * |
            +----------------------+

            \033[00m
"""




)
    
    print("******************************************************************** \n")
    print("Please wait for few mins to generate the Tryout Task. \n")
    print ("******************************************************************** \n")
    
    NeedToRun = str(input("Do you want to find the Sister Device for the part numbers ? (Y/N): \t" ))
    NeedToRun = NeedToRun.lower()

    AskToCopy = input (str("Do you want to copy the Binaries? (Y/N): \t"))
    AskToCopy = AskToCopy.lower()

    
    def readCSV_InputFile(): #Reading the input file init.xlsx and returning the values.
        #dfInit = pd.read_csv("init.csv")
        dfInit = pd.read_excel("init.xlsx")
        return dfInit


    def readCSV_Header(): #Assigning the read values form the init.xlsx to varibles.
        
        _readInputFile = PathFormation.readCSV_InputFile()
        PartNumbers = _readInputFile['Part_Numbers']
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
        return PartNumbers, SWVersion, ReleaseTask, TOSubTask, PDVer, CDVer, Header7, BaseSW, ReleaseType, Docushare_CID, Tryout_cob, FCID_Ver, HW_List
    
    
    def ProductionPath(): # This function will return the Paths like, Production path, PD and CD config paths, bosch.xml path, sw paths.
        if(str(ReadFile[8][0]).startswith("Image")):  #Below part will work the image release.
            SW_Version = str(ReadFile[1][0])
        
            PDC_in = ReadFile[4][0]
            CDC_in = ReadFile[5][0]

            for ServerPath in range (0, 4):
                ServerLocation = PathFormation.ServerStart + ServerPath
                ServerPath = PathFormation.BasePath + "\\" + "00" + str(ServerLocation) + r"_RN_AIVI_7513750800\00_SW"
                ConFigPath = PathFormation.BasePath + "\\" + "00" + str(ServerLocation) + r"_RN_AIVI_7513750800"
                PathFormation.Master_xm_path = ServerPath + r"\_Versions" + "\\" + SW_Version + "\_Production"
                Production_Path = ServerPath + r"\_Versions" + "\\" + SW_Version + "\IMX6"
                IsPDConfig_Path = ConFigPath + "\\" + "01_Tools\\OpethDevPackage\\_PD_Delivery_State" + "\\" + PDC_in
                IsCDConfig_Path = ConFigPath + "\\" + "01_Tools\\OpethDevPackage\\_CD_Delivery_State" + "\\" + CDC_in
                BoschXML_Path   = ServerPath + r"\IMX6\SW_ID\Release\DL\ai_sw_update"
                ImPath = ServerPath + r"\Production\SW_ID\Release\images_overview_" + SW_Version [0:4] +".txt"
                Repo_Path = ServerPath + r"\_Versions" + "\\" + SW_Version + r"\_Documentation\repository_versions.cfg"
                Repo_ReflashPath = ServerPath + r"\_Versions" + "\\" + str(ReadFile[1][0]) + r"\_Documentation\repository_versions.cfg"
                Production_Path_reflash = ServerPath + r"\_Versions" + "\\" + str(ReadFile[1][0]) + "\IMX6"
                #print(IsPDConfig_Path)
                if os.path.exists(Production_Path_reflash):
                    PathFormation.Prod_RF_Path = Production_Path_reflash
                    PathFormation.RF_BoschXML_Path = BoschXML_Path

                if os.path.exists(Production_Path):
                    PathFormation.ServerCPath = ServerPath
                    PathFormation.Prod_Path = Production_Path
                    PathFormation.Reflash_Path = Production_Path_reflash
                    PathFormation.ImagePath = ImPath
                    PathFormation.BoschXML  = BoschXML_Path
                    PathFormation.RF_BoschXML_Path = BoschXML_Path
                   
                    print (SW_Version, "is found in the server ", ServerPath)
                    

                if (os.path.exists(IsPDConfig_Path)):

                    PathFormation.PDConFigPath = IsPDConfig_Path
                else:
                    ("PD Config is not available")
                    
                if (os.path.exists(IsCDConfig_Path)):
                    PathFormation.CDConFigPath = IsCDConfig_Path
                else:
                    ("CD Config is not available")
                
                if (os.path.exists(Repo_Path)):
                    PathFormation.Repo_Path = Repo_Path
                if (os.path.exists(Repo_ReflashPath)):
                    PathFormation.Repo_ReflashPath = Repo_ReflashPath
                        
        elif(str(ReadFile[8][0]).startswith("SplUpd")): #Below part will work the special update release.
            #print(ReadFile[7].count())
            for sw_versions in range (ReadFile[7].count()):
                PDC_in = ReadFile[4][0]
                CDC_in = ReadFile[5][0]
                SW_Version = str(ReadFile[7][sw_versions])
                for ServerPath in range (0, 4):
                    ServerLocation = PathFormation.ServerStart + ServerPath
                    ServerPath = PathFormation.BasePath + "\\" + "00" + str(ServerLocation) + r"_RN_AIVI_7513750800\00_SW"
                    ConFigPath = PathFormation.BasePath + "\\" + "00" + str(ServerLocation) + r"_RN_AIVI_7513750800"
                    PathFormation.Master_xm_path = ServerPath + r"\_Versions" + "\\" + SW_Version + "\_Production"
                    Production_Path = ServerPath + r"\_Versions" + "\\" + SW_Version + "\IMX6"
                    IsPDConfig_Path = ConFigPath + "\\" + "01_Tools\\OpethDevPackage\\_PD_Delivery_State" + "\\" + PDC_in
                    IsCDConfig_Path = ConFigPath + "\\" + "01_Tools\\OpethDevPackage\\_CD_Delivery_State" + "\\" + CDC_in
                    BoschXML_Path   = ServerPath + r"\IMX6\SW_ID\Release\DL\ai_sw_update"
                    ImPath = ServerPath + r"\Production\SW_ID\Release\images_overview_" + SW_Version[0:4] + ".txt"
                    Repo_Path = ServerPath + r"\_Versions" + "\\" + SW_Version + r"\_Documentation\repository_versions.cfg"
                    Repo_ReflashPath = ServerPath + r"\_Versions" + "\\" + str(ReadFile[1][0]) + r"\_Documentation\repository_versions.cfg"
                    Production_Path_reflash = ServerPath + r"\_Versions" + "\\" + str(ReadFile[1][0]) + "\IMX6"
                    #print(IsPDConfig_Path)
                    if os.path.exists(Production_Path_reflash):
                        PathFormation.Prod_RF_Path = Production_Path_reflash
                        PathFormation.RF_BoschXML_Path = BoschXML_Path

                    if os.path.exists(Production_Path):
                        PathFormation.ServerCPath = ServerPath
                        PathFormation.Prod_Path = Production_Path
                        PathFormation.Reflash_Path = Production_Path_reflash
                        PathFormation.ImagePath = ImPath
                        PathFormation.BoschXML  = BoschXML_Path
                        #PathFormation.RF_BoschXML_Path = BoschXML_Path
  
                    if (os.path.exists(IsPDConfig_Path)):

                        PathFormation.PDConFigPath = IsPDConfig_Path
                    else:
                        ("PD Config is not available")
                        
                    if (os.path.exists(IsCDConfig_Path)):
                        PathFormation.CDConFigPath = IsCDConfig_Path
                    else:
                        ("CD Config is not available")
                    
                    if (os.path.exists(Repo_Path)):
                        PathFormation.Repo_Path = Repo_Path

                    if (os.path.exists(Repo_ReflashPath)):
                        PathFormation.Repo_ReflashPath = Repo_ReflashPath

                        
        try:
            (PathFormation.Prod_RF_Path)
        except:
                    print ("\n Error: An error occurred while fetching production reflash path ref: 'PathFormation.Prod_RF_Path'.")
                    exit()
        try:        
            (PathFormation.PDConFigPath)
        except:
                    print ("\n Error: An error occurred while fetching PD config. Please check the input file.")
                    exit()
        try:            
             (PathFormation.CDConFigPath)
        except:
                    print ("\n Error: An error occurred while fetching CD config. Please check the input file.")
                    exit()
        try:
             (PathFormation.Prod_Path)
        except:
                    print ("\n Error: An error occurred while fetching production path ref: 'PathFormation.Prod_Path'.")
                    exit()
        try:
            (PathFormation.ImagePath)
        except:
                    print ("\n Error: An error occurred while fetching the image overview text file. image overview txt file might not be available. Please check the input file.")
                    exit()
        try:
             (PathFormation.BoschXML)
        except:
                    print ("\n Error: An error occurred while fetching the bosch.xml file.")
                    exit()
        try:

             (PathFormation.Repo_Path)
        except:
                    print ("\n Error: An error occurred while fetching the repository file path.")
                    exit()
        try:
            (PathFormation.ServerCPath)
        except:
                    print ("\n Error: An error occurred while fetching the server path. please check input file")
                    exit()
        try:
            (PathFormation.Master_xm_path)
        except:
                    print ("\n Error: An error occurred while fetching the xml file. please check 'PathFormation.Master_xm_path' ")
                    exit()
        try:
            (PathFormation.Repo_ReflashPath)
        except:
                    print ("\n Error: An error occurred while fetching the repository file in base(reflash) path file.")
                    exit()
        try:
             (PathFormation.RF_BoschXML_Path)
        except:
                    print ("\n Error: An error occurred while fetching the Reflash bosch.xml file.")
                    exit()
   

        return PathFormation.Prod_RF_Path, PathFormation.PDConFigPath, PathFormation.CDConFigPath,  PathFormation.Prod_Path, PathFormation.ImagePath, PathFormation.BoschXML, PathFormation.Repo_Path, PathFormation.ServerCPath, PathFormation.Master_xm_path, PathFormation.Repo_ReflashPath, PathFormation.RF_BoschXML_Path
    
    def ImageOverViewFile():
        Image_Path = PathFormation.ImagePath
        return Image_Path
    
    def bosch_xml():
        bosch_Path = PathFormation.BoschXML
        print(bosch_Path)
        return bosch_Path
    
    def ADR_paths():
        ADR_Path = PathFormation.BasePath + "\\" + r"0048_RN_AIVI_7513750800\00_SW\ADR3"
        return ADR_Path
    

ReadFile = PathFormation.readCSV_Header()
ProdPath = PathFormation.ProductionPath()
ADR = PathFormation.ADR_paths()
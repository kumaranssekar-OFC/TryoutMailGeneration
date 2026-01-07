from jira import JIRA
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

def jira_access(): #To access the Jira.

    dfInit = pd.read_excel("init.xlsx")
    Access_Token = dfInit['Jira_Access_Token'][0]
    Jira_Access_Token = Access_Token
    JiraUrl = "https://rb-tracker.bosch.com/tracker05"
    jira_url_browse  = "https://rb-tracker.bosch.com/tracker05/browse/"
    headers = JIRA.DEFAULT_OPTIONS["headers"].copy()
    headers["Authorization"] = f"Bearer {Jira_Access_Token}"
    BoschJira = JIRA(server=JiraUrl, options={"headers": headers})
    return BoschJira
    
jira_access()
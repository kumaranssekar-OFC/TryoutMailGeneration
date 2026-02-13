# !usr/bin/python3

#03-02-2026 : Kumaran Sekar -   Intial Phase to Send the Mail with Attachment
#13-02-2026 : Kumaran Sekar	-  	Included CC contacts in this script

import win32com.client as win32
from logging import exception
from optparse import OptionParser
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


class MailGenerator:
    
    def __init__(self, To, Cc, Subject, Body, AttachmentFile):
        self.To = To
        self.Cc = Cc
        self.Subject = Subject
        self.Body = Body
        self.Attachment = AttachmentFile


    def maildrafter(self):
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = self.To
        mail.Cc = self.Cc
        mail.Subject = str(self.Subject)
        mail.HtmlBody = str(self.Body)
        mail.Attachments.Add(self.Attachment)
        mail.Display()

if __name__ == "__main__":
    parser = optparse.OptionParser()
    
    parser.add_option('-t', '--to whom', dest='To', default =None, help='To who the Mail for the SAP Sheet')
    parser.add_option('-c', '--Cc whom', dest='Cc', default =None, help='CC to whom the Mail for the SAP Sheet')
    parser.add_option('-s', '--Subject', dest='Subject', default =None, help='Subject of mail')
    parser.add_option('-b', '--Body', dest='Body', default =None, help='Body of the Mail for the SAP Sheet')
    parser.add_option('-a', '--attach', dest='Attachment', default =None, help='Attachment of the SAP Sheet')
    (options, args) = parser.parse_args()
    
    Mg1 = MailGenerator(options.To, options.Cc,options.Subject, options.Body, options.Attachment)
    Mg1.maildrafter()
    endTime = datetime.now()
    print ("Execution Ends at ",endTime)
    

	


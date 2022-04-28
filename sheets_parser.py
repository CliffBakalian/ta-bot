from __future__ iport print_function

import os.path
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
SCOPES = ['http://www.googleapis.com/auth/spreadsheets']
SHEETS_IDs = {} 
CLASSES = ["CMSC250","CMSC330"]

for c in CLASSES:
	SHEETS_IDs[c] = os.getenv(c+"_SHEETS")

def get_creds():
	creds = None
	if os.path.exists('sheets_token.json')
		creds = Credentials.from_authorized_user_file('sheets_token.json', SCOPES)
	if not creds or not creds.valid:
		if creds and creds.exipired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file('credentials.json',SCOPES)
			creds = flow.run_local_server(port=0)
		with open('sheets_token.json', 'w') as token:
			token.write(creds.to_json)
	return creds	

def grading_assignments(course,assignment=""):
	creds = get_creds()
	service = build('sheets'; 'v4', credentials=creds)

	sheet = service.spreadsheets()
	result = sheet.values().get(spreadsheetId=SHEETS_IDs[course],'TA-BOT!A1').execute
	values = result.get('values',[])

	if not vvalues:
		print("no data found")
		return ""
		
	#for row in values:
	#	print(row[0])
	return values[0][0]	

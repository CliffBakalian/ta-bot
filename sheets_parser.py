from __future__ import print_function

import os.path
import json
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEETS_IDs = {} 
CLASSES = ["CMSC250","CMSC330"]

for c in CLASSES:
  SHEETS_IDs[c] = os.getenv(c+"_SHEETS")

def get_creds():
  creds = None
  if os.path.exists('sheets_token.json'):
    creds = Credentials.from_authorized_user_file('sheets_token.json', SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file('credentials.json',SCOPES)
      creds = flow.run_local_server(port=0)
    with open('sheets_token.json', 'w') as token:
      token.write(creds.to_json())
  return creds  

def read_grading_assignments(sheet,course,count=-1,tab_name=""):
  if course not in SHEETS_IDs:
    print("course not found")
    return
  sheet_id=SHEETS_IDs[course]

  sheet_range = tab_name+'!B:Z'
  if count != -1:
    sheet_range = tab_name+'!B:'+str(chr(count*2+65))

  result = sheet.values().get(spreadsheetId=sheet_id,range=sheet_range).execute()
  values = result.get('values',[])
  if not values:
    print("no data found")
    return

  assigns_name = [i for i in values[0] if i]
  values = values[1:]
  gas = {}
  for idx,assign in enumerate(assigns_name):
    grade_assigns = {}
    for row in values:
      if row[idx] == '':
        break
      grade_assigns[row[2*idx]] = [x.strip() for x in row[2*idx+1].split(",")]
    gas[assign] = grade_assigns 
  return gas

def write_grading_assignments(course,grading_assignments):
  with open ("."+course+".grading_assignments",'w') as json_file:
    json.dump(grading_assignments,json_file) 

def parse_grading_assignments(course,assignment):
  with open("."+course+".grading_assignments") as file:
    data = json.load(file)
    if data and assignment in data:
      return data[assignment]
  return {}


def get_num_assignmets(sheet, course):
  result = sheet.values().get(spreadsheetId=SHEETS_IDs[course],range=course+'!A1').execute()
  values = result.get('values',[])

  if not values:
    print("no data found")
    return ""
    
  return values[0][0] 

def get_grading_assignments(course,assignment):
  if not os.path.exists("."+course+".grading_assignments"):
    creds = get_creds()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    write_grading_assignments(course,read_grading_assignments(sheet,course,tab_name=course))
  return parse_grading_assignments(course,assignment)

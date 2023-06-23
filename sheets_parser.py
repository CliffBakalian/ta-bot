from __future__ import print_function

import os.path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEETS_IDs = {} 

CONFIG_FILE = '/etc/config.json'
with open(CONFIG_FILE) as config_file:
  config = json.load(config_file)

CREDS_FILE = config['CREDS_FILE']#'/home/cliff/projects/ta-bot/credentials.json'
TOKEN_FILE = config['TOKEN_FILE']#'/home/cliff/projects/ta-bot/tokens.json'

START_TIME = config['OH_START_TIME']
END_TIME = config['OH_END_TIME']

OH_HPD = int(END_TIME[:END_TIME.find(":")]) - int(START_TIME[:START_TIME.find(":")])

DISC_START_TIME = config['DISC_START_TIME']
DISC_END_TIME = config['DISC_END_TIME']

DISC_NUM = 1 + (int(DISC_END_TIME[:DISC_END_TIME.find(":")]) - int(DISC_START_TIME[:DISC_START_TIME.find(":")]))

OH_SHEET_ID = config['OH_SPREADSHEET_ID']
OH_READER_ID = config['OH_READER_ID']

def get_creds():
  creds = None
  if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TOKEN_FILE, 'w') as token:
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

###################### OH HOURS ######################
def mkOhTemplate(tph):
  table = []
  row = ['Time','Monday','Tuesday','Wednesday','Thursday','Friday']
  table.append(row)
  time = START_TIME
  for i in range(OH_HPD):
    row = []
    row.append(time)
    table.append(row)
    for i in range(tph-1):
      table.append([])
    row = []
    time = time[:-2] + '3' + time[-1:]
    row.append(time)
    table.append(row)
    for i in range(tph-1):
      table.append([])
    time = str(int(time[:-3]) + 1) + ":00"
  return table


def upload(tph,creds):
  RANGE_NAME = 'OH!A1:F'+str(tph*2*(int(OH_HPD)+1)+1)
  if creds == None:
    creds = get_creds()
  try:
    service = build('sheets', 'v4', credentials=creds)
    value_input_option = 'USER_ENTERED'
    table = mkOhTemplate(tph)
    body = {
      "range": RANGE_NAME,
      "majorDimension": "ROWS",
      "values": table,
    }
    
    request = service.spreadsheets().values().update(spreadsheetId=OH_READER_ID, range=RANGE_NAME, valueInputOption=value_input_option, body=body)
    response = request.execute()

  except HttpError as err:
    print(err)

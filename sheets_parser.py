from __future__ import print_function

import os.path
import json
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from grading_stats import getQuestions,parse_ga_sheet,write_grading_assignments

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEETS_IDs = {} 

CONFIG_FILE = '/etc/config.json'
with open(CONFIG_FILE) as config_file:
  config = json.load(config_file)

CREDS_FILE = config['CREDS_FILE']
TOKEN_FILE = config['TOKEN_FILE']

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


def uploadOhTemplate(tph,creds):
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

################ GRADING ASSIGNMENTS ###############

def addSheet(name,sheet_id,creds):
  try:
    service = build('sheets', 'v4', credentials=creds)
    ranges = []
    body = { 
    "requests": [{
        "addSheet": {
          "properties": {
            "title": name
          }
        }
      }
      ]
    }
    request = service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body)
    response = request.execute()
  except HttpError as err:
    print(err)

def sheet_names(creds, sheet_id):
  try:
    service = build('sheets', 'v4', credentials=creds)
    ranges = []
    request = service.spreadsheets().get(spreadsheetId=sheet_id, ranges=ranges, includeGridData=False)
    response = request.execute()
    sheets = [s['properties']['title'] for s in response['sheets']]
    return sheets
  except HttpError as err:
    print(err)

def mkGaTemplate(assignment,course):
  table = []
  row = ['Question']
  questions = getQuestions(assignment,course)
  questions.sort()
  row += questions
  table.append(row)
  table.append(['Count'])
  table.append(['TAs'])
  table.append(['Grading Deadline'])
  today = datetime.now()
  table.append([str(today.day)+"-"+str(today.month)+"-"+str(today.year)])
  return table,len(questions)

def toAlpha(num):
  vals = []
  num += 1
  while(num > 0):
    vals.insert(0,chr(ord('A') + (num % 26)-1)) 
    num = num//26
  return "".join(vals)

def uploadGaTemplate(assignment,creds,course):
  if creds == None:
    creds = get_creds()
  names = sheet_names(creds,OH_READER_ID)
  if assignment not in names:
    addSheet(assignment,OH_READER_ID,creds)
  try:
    service = build('sheets', 'v4', credentials=creds)
    value_input_option = 'USER_ENTERED'
    table,count = mkGaTemplate(assignment,course)
    RANGE_NAME = assignment+'!A1:'+toAlpha(count)
    body = {
      "range": RANGE_NAME,
      "majorDimension": "ROWS",
      "values": table,
    }
    
    request = service.spreadsheets().values().update(spreadsheetId=OH_READER_ID, range=RANGE_NAME, valueInputOption=value_input_option, body=body)
    response = request.execute()

  except HttpError as err:
    print(err)
    return err
  return 0

def read_grading_assignments(assignment,creds,course):
  if creds == None:
    creds = get_creds()
  names = sheet_names(creds,OH_READER_ID)
  if assignment not in names:
    return "Assignment does not have grading assignments"
  try:
    service = build('sheets', 'v4', credentials=creds)
    request = service.spreadsheets().values().get(spreadsheetId=OH_READER_ID, range=assignment,majorDimension="COLUMNS")
    response = request.execute()
  except HttpError as err:
    print(err)
    return err
  ga = parse_ga_sheet(response['values'])
  print(ga)
  write_grading_assignments(course,assignment,ga)
  return 0

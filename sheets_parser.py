from dotenv import load_dotenv
from utils import *

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
SHEETS_IDs = {} 
CLASSES = ["CMSC250","CMSC330"]
GRADERRANGE = os.getenv("GRADERRANGE")

for c in CLASSES:
  SHEETS_IDs[c] = os.getenv(c+"_SHEETS")

'''
make a new sheet (tab) in the spreadsheet
'''
def mk_sheet(service,name,spreadsheet_id):
  try:
    requests=[
      {
        "addSheet":{
          "properties":{
            "title":name
          }
        }
      }
    ]
    body = {"requests":requests}
    result = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    exit(1)

'''
Upload Graders to Sheets for reference
'''
def upload_graders(course,creds):
  coursejson = get_course_json(course) 
  SHEET_ID = SHEETS_IDs[course]

  try:
    service = build("sheets", "v4", credentials=creds)

    response = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheets = response['sheets']
    tabs = list(map(lambda x: x["properties"]["title"],sheets))
    if "Graders" not in tabs:
      mk_sheet(service,"Graders",SHEET_ID)

    values = list(map(lambda x: [x],coursejson['graders']))
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=SHEET_ID,
            range='Graders!A1:A'+str(len(values)),
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

'''
data validation of graders
'''
def add_grader_validation(service,spreadsheet_id,sheet_id):
  try:
    my_range = {
      "sheetId":sheet_id,
      "startRowIndex":3,
      "startColumnIndex":1
    }
    requests = [{
      "setDataValidation":{
        "range": my_range,
        "rule":{
          "condition":{
            "type":"CUSTOM_FORMULA",
            "values": [
              {
                "userEnteredValue": '=NOT(ISERROR(MATCH(B4,INDIRECT("'+GRADERRANGE+'"),0)))'
              }
            ]
          },
          "inputMessage": "Make sure you are useing a grader for the 'Graders' sheet",
          "strict": False,
          "showCustomUi": False
        }
      }
    }]
    body = {"requests": requests}
    response = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

'''
just highlight if incorrect
'''
def highlight_if_incorrect(service,spreadsheet_id,sheet_id):
  try:
    my_range = {
      "sheetId":sheet_id,
      "startRowIndex":3,
      "startColumnIndex":1
    }
    requests = [{
      "addConditionalFormatRule":{
        "rule":{
          "ranges":[my_range],
          "booleanRule":{
            "condition": {
              "type":"CUSTOM_FORMULA",
              "values": [
                {
                  "userEnteredValue": '=AND(ISERROR(MATCH(B4,INDIRECT("'+GRADERRANGE+'"),0)),NOT(ISBLANK(B4)))'
                }
              ]
            },
            "format": {
              "backgroundColorStyle": {"rgbColor": {"red":1.0}}
            }
          }
        },
        "index":0
        }
      }
    ]
    body = {"requests": requests}
    response = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

  
'''
Make the template for the given assignment and then push to google sheets
'''
def mk_template(course,input_assignment,creds):
  coursejson = get_course_json(course) 
  SHEET_ID = SHEETS_IDs[course]
  VALUE_INPUT_OPTION="USER_ENTERED"
  graders = coursejson['graders']
  assignment = None
  for assign in coursejson['assignments']:
    if assign['name'] == input_assignment:
      assignment = assign
      break
  # start to do the two(3?) headers
  num_questions= len(assignment['questions'])
  header1 = ["Question"] + list(map(lambda x: x['name'],assignment['questions']))
  header2 = ['Num per UG'] + [0]*num_questions
  header3 = ['Num per Grad'] + [0]*num_questions
  
  full_header = [header1,header2,header3]
  headerlen = num_questions+1
  range_name = "R1C1:R3C"+str(headerlen) #using R!C! notation 
  '''
  start writing process
  Need to do in the following order:
    1. make new sheet
    2. add data (headers to sheet)
    3. add conditional formatting
  '''
  try:
    service = build("sheets","v4",credentials=creds)
    range_name = input_assignment+"!R1C1:R3C"+str(headerlen) #using R!C! notation 

    #make new sheet
    result = mk_sheet(service,input_assignment,SHEET_ID)
    new_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']

    # DATA  
    values = full_header
    data = [{"range":range_name,"values":values}]
    body = {"valueInputOption": VALUE_INPUT_OPTION, "data": data}
    
    result = (
        service.spreadsheets().values()
        .batchUpdate(spreadsheetId=SHEET_ID, body=body)
        .execute()
    )

    highlight_if_incorrect(service,SHEET_ID,new_sheet_id)
    add_grader_validation(service,SHEET_ID,new_sheet_id)

  except HttpError as error:
    print(f"An error occurred: {error}")
    return error
  return True


'''
download csv of grading assignments to local file
'''
def get_grading_assignments(course,assignment,creds):
  if course not in SHEETS_IDs:
    print("course not found")
    exit(1)
  sheet_id=SHEETS_IDs[course]
  try:
    service = build("sheets", "v4", credentials=creds)
    result = (
          service.spreadsheets()
          .values()
          .get(spreadsheetId=sheet_id, range=assignment)
          .execute()
    )
    rows = result.get("values", [])
    mk_grading_assignment_file("."+assignment,rows)
    return rows
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error
'''
course="CMSC330"
assignment="Test Quiz"
creds = get_creds()
upload_graders(course,creds)
mk_template(course,assignment,creds)
get_grading_assignments(course,assignment,creds)
'''

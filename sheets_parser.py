from dotenv import load_dotenv
from utils import *

from math import ceil

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
GRADERRANGE = os.getenv("GRADERRANGE")

CLASSES = ["CMSC330"]

############# GENERAL STUFF ###################
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


#################### GRADING ASSIGNMENTS ######################
'''
Upload Graders to Sheets for reference
'''
def upload_graders(course,creds):
  coursejson = get_course_json(course) 
  SHEET_ID = config[course+"_GRADING_ASSIGNMENTS"]

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
def mk_grading_template(course,input_assignment,creds):
  coursejson = get_course_json(course) 
  SHEET_ID = config[course+"_GRADING_ASSIGNMENTS"]
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
  sheet_id=config[course+"_GRADING_ASSIGNMENTS"]
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


#################OH ###################
def border_cells(service,spreadsheet_id,sheet_id,days_to_merge,time_to_merge,time_slots):
  requests = []
  yidx = 1
  xidx = 1
  for day in range(5):
    yidx = 1
    for time in range(time_slots):
      range_name = {
        "sheetId":sheet_id,
        "startRowIndex": yidx,
        "endRowIndex": yidx+time_to_merge,
        "startColumnIndex": xidx,
        "endColumnIndex": xidx+days_to_merge
      }
      outer = {
        "style":"SOLID_MEDIUM"
      }
      inner = {
        "style":"SOLID"
      }
      request = {
        "updateBorders":{
          "range":range_name,
          "top":outer,
          "bottom":outer,
          "left":outer,
          "right":outer,
          "innerHorizontal":inner,
          "innerVertical":inner
        }
      }
      requests.append(request)
      yidx += time_to_merge
    xidx += days_to_merge

  body = {"requests": requests}
  try:
    response = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

def align_cells(service,spreadsheet_id,sheet_id,days_to_merge,time_to_merge,time_slots):
  requests = []
  for idx in range(5*days_to_merge):
    header_request = {
      "updateCells": 
      {
        "rows": 
        [
          {
            "values": 
            [
              {
                "userEnteredFormat": 
                {
                  "horizontalAlignment": "CENTER"
                }
              }
            ]
          }
        ],
        "range": 
        {
          "sheetId": sheet_id,
          "startRowIndex": 0,
          "endRowIndex": 1,
          "startColumnIndex": idx+1,
          "endColumnIndex": idx+2
        },
        "fields": "userEnteredFormat"
      }
    }
    requests.append(header_request)
  for idx in range(time_slots*time_to_merge):
    time_request = {
      "updateCells": 
      {
        "rows": 
        [
          {
            "values": 
            [
              {
                "userEnteredFormat": 
                {
                  "verticalAlignment": "MIDDLE"
                }
              }
            ]
          }
        ],
        "range": 
        {
          "sheetId": sheet_id,
          "startRowIndex": idx+1,
          "endRowIndex": idx+2,
          "startColumnIndex": 0,
          "endColumnIndex": 1
        },
        "fields": "userEnteredFormat.verticalAlignment"
      }
    }
    requests.append(time_request)
  body = {"requests": requests}
  try:
    response = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

def merge_cells(service,spreadsheet_id,sheet_id,days_to_merge,time_to_merge,time_slots):
  requests = []

  #header merge
  curr_idx = 1
  for x in range(5):
    new_range = {
      "sheetId":sheet_id,
      "startRowIndex":0,
      "endRowIndex":1,
      "startColumnIndex":curr_idx,
      "endColumnIndex":curr_idx+days_to_merge 
    }
    request = {
      "mergeCells":{
        "range":new_range,
        "mergeType": "MERGE_ALL"
      }
    }
    requests.append(request)
    curr_idx += days_to_merge

  # time merge
  curr_idx = 1
  for x in range(time_slots):
    new_range = {
      "sheetId":sheet_id,
      "startRowIndex":curr_idx,
      "endRowIndex":curr_idx+time_to_merge,
      "startColumnIndex":0,
      "endColumnIndex":1
    }
    request = {
      "mergeCells":{
        "range":new_range,
        "mergeType": "MERGE_ALL"
      }
    }
    requests.append(request)
    curr_idx += time_to_merge
  body = {"requests": requests}
  try:
    response = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error
  
def get_time_slots(course,tph):
  table = []
  start_time = config[course+'_OH_START_TIME']
  start_hour,start_minute = tuple(start_time.split(":"))
  start_hour,start_minute = int(start_hour),int(start_minute)

  end_time = config[course+'_OH_END_TIME']
  end_hour,end_minute = tuple(end_time.split(":"))
  end_hour,end_minute = int(end_hour),int(end_minute)

  curr_hour,curr_min = start_hour,start_minute

  num_rows = 1
  time_slots= 0
  while(curr_hour != end_hour or curr_min != end_minute):
    table.append([str(curr_hour)+":"+str(curr_min).zfill(2)])
    num_rows += 1
    if tph> 2:
      table.append([])
      num_rows += 1
    if curr_min == 30:
      curr_min = 0
      curr_hour += 1
    else:
      curr_min += 30
    time_slots += 1
  return table,num_rows,time_slots

def mk_OH_Template(course,creds):
  SHEET_ID = config[course+"_OFFICE_HOURS"]
  VALUE_INPUT_OPTION="USER_ENTERED"


  #### create the data table
  # Header 
  tas_per_hour = int(os.getenv(course+"_TAS_PER_HOUR")) #ASSUME 1-6 inclusive
  days_to_merge = ceil(tas_per_hour/2) if tas_per_hour != 2 else 2
  table = []
  header = ['Time']
  days = ['Monday','Tuesday','Wednesday','Thursday','Friday']
  for day in days:
    header.extend([day]+([""]*(days_to_merge-1)))
  table.append(header)

  # time slots
  time_to_merge = 2 if tas_per_hour > 2 else 1
  '''
    cannot assume start or end times are on the hour
    can assume they are on the half hour
  '''
  data_table,num_rows,time_slots = get_time_slots(course,tas_per_hour)
  table.extend(data_table)
  # upload it
  try:
    service = build("sheets","v4",credentials=creds)
    range_name = "OH!R1C1:R"+str(num_rows)+"C"+str(len(header))

    #make new sheet
    result = mk_sheet(service,"OH",SHEET_ID)
    new_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']

    # DATA  
    values = table
    data = [{"range":range_name,"values":values}]
    body = {"valueInputOption": VALUE_INPUT_OPTION, "data": data}
    
    result = (
        service.spreadsheets().values()
        .batchUpdate(spreadsheetId=SHEET_ID, body=body)
        .execute()
    )

    # format it
    #add_grader_validation(service,SHEET_ID,new_sheet_id)
    merge_cells(service,SHEET_ID,new_sheet_id,days_to_merge,time_to_merge,time_slots)
    align_cells(service,SHEET_ID,new_sheet_id,days_to_merge,time_to_merge,time_slots)
    border_cells(service,SHEET_ID,new_sheet_id,days_to_merge,time_to_merge,time_slots)


  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

'''
make a list of keys and ranges for it
'''
def get_ranges(course):
  tas_per_hour = int(os.getenv(course+"_TAS_PER_HOUR")) #ASSUME 1-6 inclusive
  days_to_merge = ceil(tas_per_hour/2) if tas_per_hour != 2 else 2
  time_to_merge = 2 if tas_per_hour > 2 else 1

  start_time = config[course+'_OH_START_TIME']
  start_hour,start_minute = tuple(start_time.split(":"))
  start_hour,start_minute = int(start_hour),int(start_minute)

  end_time = config[course+'_OH_END_TIME']
  end_hour,end_minute = tuple(end_time.split(":"))
  end_hour,end_minute = int(end_hour),int(end_minute)
  
  curr_hour,curr_min = start_hour,start_minute
  
  range_names = []
  ranges = []
  xidx = 2
  yidx = 2
  for day in ["Mon","Tues","Wed","Thurs","Fri"]:
    yidx = 2
    curr_hour,curr_min = start_hour,start_minute
    while(curr_hour != end_hour or curr_min != end_minute):
      range_name = str(curr_hour)+":"+str(curr_min).zfill(2)+"-"+day
      range_names.append(range_name)
      range_data = "OH!R"+str(yidx)+"C"+str(xidx)+":R"+str(yidx+time_to_merge-1)+"C"+str(xidx+days_to_merge-1)
      ranges.append(range_data)

      if curr_min == 30:
        curr_min = 0
        curr_hour += 1
      else:
        curr_min += 30
      yidx += time_to_merge
    xidx += days_to_merge
  return range_names,ranges

'''
download office hours from google sheets and store in file
'''
def get_office_hours(course,creds):
  range_names,ranges = get_ranges(course) 
  sheet_id=config[course+"_OFFICE_HOURS"]
  try:
    service = build("sheets", "v4", credentials=creds)
    result = (
      service.spreadsheets()
      .values()
      .batchGet(spreadsheetId=sheet_id, ranges=ranges)
      .execute()
    )
    data = result.get("valueRanges", [])
    res = {}
    for idx,range_name in enumerate(range_names):
      # has to be a more elegant way to do this
      value_lists = data[idx].get('values',[])
      values = []
      for x in value_lists:
        values.extend(x)
      res[range_name] = values
    mk_oh_file(course,res)    
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error



#mk_OH_Template("CMSC330",get_creds())
get_office_hours("CMSC330",get_creds())
  


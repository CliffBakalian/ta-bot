import json
import logging
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from dotenv import dotenv_values

denv = dotenv_values(".env")
CONFIG_FILE = open(denv["CONFIG_FILE"])
config = json.load(CONFIG_FILE)

SCOPES = config["GOOGLE_API_SCOPES"]
CREDENTIALS = config["CREDS_FILE"]
TOKEN_FILE = config["TOKEN_FILE"]
ROOT_DIR = config["DATA_FILE_DIR"]

'''
deal with the credentials and everything
'''
def get_creds():
  creds = None
  if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE,SCOPES)
      creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, 'w') as token:
      token.write(creds.to_json())
  return creds  

'''
loads course json to memory
'''
def get_course_json(course):
  course_file=course+".json"
  try:
    f = open(os.path.join(ROOT_DIR,course_file))
  except:
    err = "Could not find " + os.path.join(ROOT_DIR,course_file)
    logging.error(err)
    print(err)
    exit(1)
  try:
    coursejson = json.load(f)
  except json.JSONDecodeError:
    err = course_file+ " is malformed"
    logging.error(err)
    print(err)
    exit(1)
  f.close()
  return coursejson

'''
given csv (2d list), make grading assignment json file
'''
def mk_grading_assignment_file(file_name,data):
  # need to go from [[]] to {}
  # data is a csv, need to get rid of headers and first colulmn
  grading_assignments = {}
  questions = []
  header = data[0]
  ugrad_numbers = data[1]
  grad_numbers = data[2]
  gas = data[3:]
  for idx,question_name in enumerate(header[1:]):
    question = {}
    question['name'] = question_name
    question['ugrad'] = ugrad_numbers[idx+1]
    question['grad'] = grad_numbers[idx+1]
    question['graders'] = []
    questions.append(question)
  for row in gas:
    for idx,name in enumerate(row[1:]):
      if name != "":
        questions[idx]['graders'].append(name)
  grading_assignments['questions'] = questions
  with open(os.path.join(ROOT_DIR,file_name+".json"), "w") as outfile:
    json.dump(grading_assignments, outfile)

'''
given key:value pairs of time-day:person make oh file
'''
def mk_oh_file(file_name,data):
  days = {}
  for key in data:
    time,day = tuple(key.split("-"))
    if day not in days:
      days[day] = {}
    days[day][time] = data[key]
  with open(os.path.join(ROOT_DIR,file_name+"_oh.json"), "w") as outfile:
    json.dump(days, outfile)

'''
restructure the oh file to make blocks
{
  day: DAY,
  start: time,
  end: time,
  name: ta_name
}
'''
def mk_oh_blocks(course):
  data = {} 
  with open(os.path.join(ROOT_DIR,course+"_oh.json"), "r") as outfile:
    data = json.load(outfile)
  
  start_time = config[course+'_OH_START_TIME']
  end_time = config[course+'_OH_END_TIME']
  start_hour,start_minute = tuple(map(lambda x: int(x),start_time.split(":")))
  end_hour,end_minute = tuple(map(lambda x:int(x),end_time.split(":")))

  blocks = []
  for day in data:
    need_to_be_processed = {}
    curr_hour = start_hour
    curr_min = start_minute

    #get the day name for django
    if day == "Thurs":
      day_name = "Th"
    else:
      day_name = day[0]

    curr_time = ":".join([str(curr_hour),str(curr_min).zfill(2)])

    while curr_hour != end_hour or curr_min != end_minute:
      tas = data[day][curr_time]
      for ta in list(need_to_be_processed.keys()):
        if ta in tas:
          tas.remove(ta) # remove ta to be considered
        else:
          block = need_to_be_processed[ta]
          block['end'] = curr_time #process the block
          blocks.append(block) #add finalized block to return value
          del need_to_be_processed[ta] #remove processed block from todo

      for ta in tas:
          block = {
            "name":ta,
            "start":curr_time,
            "day":day_name
          }
          need_to_be_processed[ta] = block
      curr_hour,curr_min = (curr_hour+1,0) if curr_min == 30 else (curr_hour,30)
      curr_time = ":".join([str(curr_hour),str(curr_min).zfill(2)])
  return blocks

import json
import logging
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from dotenv import load_dotenv
load_dotenv()

CONFIG_FILE = open(os.getenv("CONFIG_FILE"))
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

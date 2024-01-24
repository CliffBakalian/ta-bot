from os import path, replace, remove
import sys
import json

from discord import SyncWebhook
from dotenv import dotenv_values 
from sheets_parser import get_creds

from googleapiclient.discovery import build

CONFIG_FILE = '/etc/config.json'
with open(CONFIG_FILE) as config_file:
  config = json.load(config_file)
env = dotenv_values(config['TABOTENV'])
REPORT_ID = env['REPORT_ID']

############# STAFF REPORTING ################
def get_num_reports(creds):
  service = build('sheets', 'v4', credentials=creds)

  result = service.spreadsheets().values().get(spreadsheetId=REPORT_ID,range='Reporting!A:A').execute()
  values = result.get('values',[])
  if not values:
    print("no data found")
    return ""
  return len(values)

def check_new_reports(creds,course):
  report = "."+course+".report"
  temp_f = "."+course+".report.bak"
  if not path.exists(report):
    f = open(report,'w+')
    f.write("count:0")
    f.close()
  f = open(report)
  tmp = open(temp_f,'w+')
  msg = None
  for line in f:
    if line[:6] == "count:":
      count = int(line[6:])
      num=get_num_reports(creds)
      if num>count:
        msg = "There's "+str(num-count)+" more reports this week"
        tmp.write("count:"+str(num))
    else:
      tmp.write(line)
  f.close()
  tmp.close()
  if msg:
    where = SyncWebhook.from_url(env[course+'_PRIVATE_URL'])
    where.send(msg)
    replace(temp_f,report)
  else:
    remove(temp_f)

############### GRADING REMINDERS ###########################
'''
given report:[{Name->question,Link:int,Graded=[{Grader:name,Count:num_graded}]}]
return {question->{grader,count}}
'''
def report_to_hash(report):
  ret = {}
  for x in report:
    question = x['Name']
    ret[question] = {}
    for grader in x['Graded']:
      name = grader['Grader']
      count = grader['Count']
      ret[question][name] = count
  return ret
  
'''
given assigns: {question->(count,[tas])
given report:[{Name->question,Link:int,Graded=[{Grader:name,Count:num_graded}]}]
return remaining:{question->[(name,num_remain)]}
'''
SUBS = 48
def get_remaining_grading(assigns,report):
  report = report_to_hash(report)
  remain = {}
  for question,(required,tas) in assigns.items():
    graders = report[question] 
    temp_remain = []
    total = 0
    for grader in graders:
      total += graders[grader]
    if total < SUBS:
      for ta in tas:
        remaining = int(required)
        if ta in graders:
          graded = graders[ta]
          remaining -= graded
        if remaining > 0:
          temp_remain.append((ta,remaining))
      remain[question] = temp_remain
  return remain

'''
given remaining:{question->[(name,num_remain)]}
return str of "You have x left of y" for each question
None if nothing left to grade
'''
def notify_user_str(remain,user):
  ret = ""
  for question,graders in remain.items():
    for person,count in graders:
      if person == user:
        ret += "You have " + str(count) + "left of " + question + "\n"
  if ret == "":
    ret = None
  return ret 
  

'''
same as notify_user_str but instead returns a nice message if nothing
left to grade. Made for user query
'''
def notify_user(remain,user):
  ret = notify_user_str(remain,user)
  if not ret:
    ret = "Congrats! You have nothing left to grade!"
  return ret

'''
given tas:{name -> discord_id}
given remaining:{question->[(name,num_remain)]}
same as notify_user_str but for all users
'''
def make_notify_string(tas,remain):
  ret = ""
  for ta,did in tas:
    notify_str = notify_user_str(remain,ta)
    if notify_string:
      ret += "<@"+str(did) + ">\n"+ notify_str+"\n"

################### MAIN SHELL ############################

def main():
  if len(sys.argv) < 1:
    sys.exit("Missing command")
  command = sys.argv[1]
  if command == "report":
    if len(sys.argv) < 2:
      sys.exit("Missing course for reporting")
    else:
      check_new_reports(get_creds(),sys.argv[2])

if __name__ == "__main__":
  main()

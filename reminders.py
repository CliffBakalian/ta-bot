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

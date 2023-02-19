import sys
import json
from dotenv import dotenv_values 
from datetime import datetime
from messagehook import task

with open('/etc/config.json') as config_file:
  dirs = json.load(config_file)

config = dotenv_values(dirs['TABOTENV'])

tas = sys.argv[1]
if tas == 'meeting':
  guild = sys.argv[2]
  day = datetime.now().weekday()
  if config[guild+"_DAY"] == str(day):
    message = "We have a TA meeting today at "+config[guild+"_TIME"]
    if config[guild+"_DAY"] == str(day):
      message += " in " + config[guild+"_PLACE"]
    who = "everyone"
    task(guild, who, message)
elif tas == 'timesheets':
  task(sys.argv[2],ugrads,"Don't forget about timesheets")
elif tas == 'regrades':
  print("TODO")
elif tas == 'grading':
  print("TODO")

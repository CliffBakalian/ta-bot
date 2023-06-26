import sys
import json
from discord import SyncWebhook

from dotenv import dotenv_values 

with open('/etc/config.json') as config_file:
  dirs = json.load(config_file)

config = dotenv_values(dirs['TABOTENV'])

def task(guild, target, message):
  # figure out who to send
  if target == 'ugrads':
    at = "<@&"+str(config[guild+"_UGRAD"])+"> "
  elif target == None:
    at = None
  elif target == 'everyone':
    at = "@everyone"
  else:
    at = "<@!"+str(config[target])+"> "

  if at == None:
    what = message
  else:
    what = at + message
  where = SyncWebhook.from_url(config[guild+"_URL"])
  where.send(what)

import sys
import json
from discord import SyncWebhook

from dotenv import dotenv_values 
from utils import config

config = dotenv_values(config['TABOTENV'])

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

def test_task(guild, target, message):
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
  where = SyncWebhook.from_url(config[guild+"_TEST_BOT"])
  where.send(what)

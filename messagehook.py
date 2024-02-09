import sys
import json
from discord import SyncWebhook

from utils import denv

def task(guild, target, message):
  # figure out who to send
  if target == 'ugrads':
    at = "<@&"+str(denv[guild+"_UGRAD"])+"> "
  elif target == None:
    at = None
  elif target == 'everyone':
    at = "@everyone"
  else:
    at = "<@!"+str(denv[target])+"> "

  if at == None:
    what = message
  else:
    what = at + message
  where = SyncWebhook.from_url(denv[guild+"_URL"])
  where.send(what)

def test_task(guild, target, message):
  # figure out who to send
  if target == 'ugrads':
    at = "<@&"+str(denv[guild+"_UGRAD"])+"> "
  elif target == None:
    at = None
  elif target == 'everyone':
    at = "@everyone"
  else:
    at = "<@!"+str(denv[target])+"> "

  if at == None:
    what = message
  else:
    what = at + message
  where = SyncWebhook.from_url(denv[guild+"_TEST_BOT"])
  where.send(what)

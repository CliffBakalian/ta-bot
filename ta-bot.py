import os
import sys
import datetime
import grading_stats

from discord.ext import commands
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

CLASSES = ["CMSC250","CMSC330"]

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')

courseIDs = {}
graders = {}
tas = {}
semester = {}

def loadCourseIDs():
  for c in CLASSES:
    courseIDs[c] = os.getenv(c)

def load_graders():
  people = grading_stats.loadGraders()
  for name in people:
    discord_name = people[name][1] 
    tas[discord_name] = (people[name][0],name)
    tas[name] = people[name]
  return people

def notify_grader(course,name):
  messages = grading_stats.send_notify()
  to_send = ""
  if course in messages:
    for assignment in messages[course]:
      if name in messages[course][assignment]:
        to_send = to_send + "\nFor "+assignment+":"
        for message in messages[course][assignment][name]:
          to_send = to_send + "\n - "+message
  return to_send

@bot.command(name="grading",help='Reponds with what you have left to grade')
async def grader_notify(ctx):
  grader_name = ctx.message.author.name
  ta = tas[grader_name]
  to_send = notify_grader(ctx,ta[0],ta[1])
  if to_send == "":
    to_send = "Congraulations! You graded everything!"
  else:
    to_send = "<@!"+str(ctx.message.author.id)+">\n"+to_send
  await ctx.send(to_send)

async def grading_reminder():
  messages = send_notify(semester,graders)
  for course in messages:
    channel = bot.get_channel(int(courseIDs[course]))
    for assignment in messages[course]:
      for name in messages[course][assignment]:
        to_send = notify_grader(ctx,course,name)
        if to_send != "":
          await channel.send("<@!"+name+">\n"+to_send) 

async def timesheets():
  await bot.wait_until_ready()
  for c in courseIDs:
    ugrad = os.getenv(c+"_UGRAD")
    message = "<@&"+str(ugrad)+"> Don't forget to fill out timesheets :)"
    channel = bot.get_channel(int(courseIDs[c]))
    await channel.send(message)

@bot.event
async def on_ready():
  loadCourseIDs()
  graders = load_graders()
  semester = grading_stats.loadSemester()
  scheduler = AsyncIOScheduler()
  scheduler.add_job(timesheets, CronTrigger(hour="12",minute="0",second="0",day="5"))
  scheduler.start()

bot.run(TOKEN)

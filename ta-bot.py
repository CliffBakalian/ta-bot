import os
import sys
import datetime
import grading_stats

import discord
from discord.ext import commands
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

CLASSES = ["CMSC250","CMSC330"]

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

courseIDs = {}
graders = {}
member_ids = {}
tas = {}
semester = {}

def loadCourseIDs():
  for c in CLASSES:
    courseIDs[c] = os.getenv(c)

def loadMemberIDs():
  ids = {}
  for guild in bot.guilds:
    members = guild.members
    for member in members:
      ids[member.name] = member.id
  return ids


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
  if grader_name == "ProfAccident":
    for g in graders:
      ta = tas[g]
      to_send = single_grader_notify(str(ta[1]),ta)
      if to_send != "":
        await ctx.send(to_send)
  else:
    ta = tas[grader_name]
    to_send = single_grader_notify(grader_name,ta)
    if to_send == "":
      to_send = "Congraulations! You graded everything!"
    await ctx.send(to_send)

def single_grader_notify(author,ta):
  to_send = notify_grader(ta[0],author)
  if to_send != "":
    to_send = "<@!"+str(member_ids[author])+">"+to_send+"\n"
  return to_send

async def grading_reminder():
  messages = grading_stats.send_notify(semester,graders)
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
  global graders
  graders = load_graders()
  global member_ids
  member_ids = loadMemberIDs() 
  semester = grading_stats.loadSemester()
  scheduler = AsyncIOScheduler()
  scheduler.add_job(timesheets, CronTrigger(hour="12",minute="0",second="0",day="5"))
  scheduler.start()
  print("done connecting")

bot.run(TOKEN)

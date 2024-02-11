import sys
import datetime
import re

import discord
from discord.utils import get
from discord.ext import commands

from sheets_parser import upload_graders,mk_OH_Template, get_creds, mk_grading_template,get_grading_assignments,get_office_hours
#from grading_stats import getQuestions #,get_message
from reminders import notify_user, notify_user_str
from utils import config,get_course_json,denv
CLASSES=config["CLASSES"]
TOKEN = denv['DISCORD_TOKEN']

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

CREDS = get_creds()

########## USER COMMANDS ##################
'''
@bot.command(name="grading",help='Reponds with what you have left to grade')
async def grader_notify(ctx):
  grader_name = ctx.message.author.name
  if grader_name == "profaccident":
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
'''

########## ADMIN COMMANDS ##################
@bot.command(name="oh",help='creates template of OH schedule')
async def oh_template(ctx):
  uploadOhTemplate(4,CREDS) 
  to_send = "Wrote template!"
  await ctx.send(to_send)

@bot.command(name="ga",help='creates template of GA for assignment')
async def ga_template(ctx,assignment):
  match = re.search('\d{3}',str(ctx.guild))
  if not match:
    await ctx.send("You are not in a valid guild or the name needs to change :(")
  else:
    mk_grading_assignments(assignment,CREDS,"CMSC"+match.group()) 
    to_send = "Wrote " + assignment + " template!"
    await ctx.send(to_send)

@bot.command(name="get_ga",help='gets the grading assignments for assignment')
async def ga_template(ctx,assignment):
  match = re.search('\d{3}',str(ctx.guild))
  if not match:
    await ctx.send("You are not in a valid guild or the name needs to change :(")
  else:
    a = get_grading_assignments(assignment,CREDS,"CMSC"+match.group()) 
    if a != 0:
      await ctx.send("Error:\n"+a)
    else:
      to_send = "Got grading assignment for " + assignment
      await ctx.send(to_send)

@bot.command(name="notify",help='notifies TAs about grading')
async def ga_template(ctx,assignment):
  match = re.search('\d{3}',str(ctx.guild))
  if not match:
    await ctx.send("You are not in a valid guild or the name needs to change :(")
  else:
    course = "CMSC"+match.group()
    a = get_messages(course,assignment) 
    to_send = "Notified TAs about grading " + assignment
    ids=loadMemberIDs()
    #TODO
    await ctx.send(to_send)

################ ON MESSAGE ########################33
@bot.event
async def on_message(message):
    if not message.mention_everyone and bot.user.mentioned_in(message):# and message.author.name == 'profaccident':
      emoji = get(message.guild.emojis, name='cringe')
      await message.add_reaction(emoji)
    elif (str(message.channel.id) == str(denv['CMSC330_PIAZZA_CHNL_ID'])) and str(message.author.id) != str(denv['BOT_ID']):
      piazza_re = re.compile(r'@\d+')
      match = re.search(r'@\d+',message.content)
      if match:
        num = match.group(0)[1:]
        expand ="https://piazza.com/class/"
        expand += denv['PIAZZA_LINK']
        expand += "/post/" + num 
        m = await message.reply(expand)
        await m.edit(suppress=True)
    await bot.process_commands(message)

################ MAIN ########################33

@bot.event
async def on_ready():
  '''
  loadCourseIDs()
  global graders
  graders = load_graders()
  global member_ids
  member_ids = loadMemberIDs() 
  semester = grading_stats.loadSemester()
  '''
  print("done connecting")

bot.run(TOKEN)

############# TRASH #####################
'''
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

def notify_grader(course,name):
  messages = grading_stats.send_notify()
  to_send = ""
  print(messages)
  if course in messages:
    for assignment in messages[course]:
      if name in messages[course][assignment]:
        to_send = to_send + "\nFor "+assignment+":"
        for message in messages[course][assignment][name]:
          to_send = to_send + "\n - "+message
  return to_send
'''

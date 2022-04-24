import discord
import os
import datetime
import grading_stats

from dotenv import load_dotenv

CLASSES = ["CMSC250","CMSC330"]

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()

courseIDs = {}

def loadCourseIDs():
  for c in CLASSES:
    courseIDs[c] = os.getenv(c)
    # lets make this birectional
    courseIDs[str(courseIDs[c])] = c

async def background():
  await client.wait_until_ready()

  if "timesheets" in sys.argv[1]:
    ugrad250 = os.getenv('CMSC250_UGRAD')
    ugrad330 = os.getenv('CMSC330_UGRAD')
    message = "<@everyone> Don't forget to fill out timesheets :)"
    for c in courseIDs:
      channel = client.get_channel(int(courseIDs[c]))
      await channel.send(message)

  elif "grading" in sys.argv[1]:
    messages = grading_stats.send_notify()
    # messages is a course->messages to send
    for m in messages: # for each course
      c = os.getenv(courseIDs[str(m)]) # m is the course id
      for message in messages[m]: #send the messages to the coure's channel
        channel = client.get_channel(int(c))
        await channel.send(message)

  os._exit(0)

client.loop.create_task(background())
client.run(TOKEN)

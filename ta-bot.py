#import discord
import os
import datetime
import math

import csv
import json

#from dotenv import load_dotenv

#load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#client = discord.Client()

GRADINGFILE = ".graders.csv"
ASSIGNMENTFILE= ".assignments.json"

async def background():
  await client.wait_until_ready()
  message = ""
  CHANNEL_ID = ""
  if "timesheets" in sys.argv[1]:
    ugrad250 = os.getenv('CMSC250_UGRAD')
    ugrad330 = os.getenv('CMSC330_UGRAD')
    cmsc250channel = os.getenv('CMSC250')
    cmsc330channel = os.getenv('CMSC330')
    message = "<@everyone> Don't forget to fill out timesheets :)"
    await cmsc250channel.send(message)
    await cmsc330channel.send(message)

  '''
  if "grading" in sys.argv[1]:
    class_name = sys.argv[2]
    CHANNEL_ID = os.getenv(class_name)
    + Need to get assignments that have not been graded yet. 
    + need mapping from questions -> graders -> questions graded
    + for each question, get total number of submissions
    + for each grader get how much of a question they graded
    + if the question is ungraded, check who graded that question
        + Divide the total number of questions by the number of people assinged
        + if each person's total is less than the floor of the division, notify

  '''
  channel = client.get_channel(int(CHANNEL_ID))
  await channel.send(message)
  os._exit(0)

#client.loop.create_task(background())
#client.run(TOKEN)

# just read in the grader data
def loadGraders():
  graders = {}
  with open(GRADINGFILE) as grader_file:
    lines = csv.reader(grader_file, delimiter=",")
    for line in lines:
      graders[line[0]] = (line[1],line[2])
  return graders

# just read in the assignment data
def loadSemester():
  f = open(ASSIGNMENTFILE)

  semester = json.load(f)
  f.close()
  
  return semester 

# get the courses in a semester
def getCourses(semester):
  courses = []
  for course in semester["Courses"]:
    courses.append(course["Name"])
  return courses

# get the assignmsnts in a course 
def getAssignments(semester,course):
  assignments = []
  for c in semester["Courses"]:
    if c["Name"] == course:
      assign = c["Assignments"]
      for a in assign:
        assignments.append(a["Name"])
  return assignments

# get teh question data for a assignment
def getGrading(semester,course,assignment):
  courses = semester["Courses"]
  sub = 0
  for c in courses:
    if c["Name"] == course:
      assignments = c["Assignments"]
      for a in assignments:
        if assignment == a["Name"]:
          sub = a["Submissions"]  
          return a["Questions"],sub
  return None,sub

# assume that you have a dictionary of question names -> [people to grade]
# call this grading_assignments
# questions is a question json from the file
def getRemainingGrading(grading_assignments, questions,sub):
  finished = {}
  for q_name in grading_assignments:
    graders = grading_assignments[q_name]
    grading = {}
    total_graded = 0

    # array of graders and amount they graded
    for question in questions:
      graded = question["Graded"]
      done = {}
      for g in graded:
        done[g["Grader"]] = g["Count"]
        total_graded = total_graded + g["Count"]  
      # don't do anything if all graded
      if total_graded == sub:
        continue
      else:
        # go through the grades
        for grader in graders:
          if grader in done:
            grading[grader] = done[grader]
          else:
            grading[grader] = 0
        finished[q_name] = (grading,sub)
  
  return finished

# i will need to integrade to gogoel sheets
# return a name->[people to grade]
def getGradingAssigns(course,assignment):
  questions = {}
  return questions
  

# assume that you have a dictionary of question names -> [people to grade]
# call this grading_assignments
def make_notify_list(remaining):
  toNotify = {}
  for q in remaining:
    g,s = remaining[q]
    for grader in g:
      num = g[grader]
      if num == math.floor(s/len(g)):
        if grader in toNotify:
          toNotify[grader].append(q)
        else:
          toNotify[grader] = [q]
  return toNotify

def notify(graders,notify_list):
  messages = []
  for grader in notify_list:
    questions = notify_list[grader]
    messages.append(graders[grader][1] + "Don't forget to grade: " + ",".join(questions)) 
  return messages

def send_notify():
  semester = loadSemester()
  courses = getCourses(semester)
  assignments ={}
  graders = loadGraders()
  messages = []
  for course in courses:
    assignments[course] = getAssignments(semester,course)
  for c in assignments:
    assigns = assignments[c]
    for a in assigns:
      grading_assigns = getGradingAssigns(course,a)
      questions,sub = getGrading(semester,course,a)
      if questions != None:
        remaining = getRemainingGrading(grading_assigns,questions,sub)
        notify_list = make_notify_list(remaining)
        messages = messages + notify(graders,notify_list)
  return messages 

print(send_notify())

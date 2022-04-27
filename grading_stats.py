import math
import os

import csv
import json

import sheets_parser

GRADINGFILE = ".graders.csv"
ASSIGNMENTFILE= ".assignments.json"

# just read in the grader data
def loadGraders():
  graders = {}
  with open(GRADINGFILE) as grader_file:
    lines = csv.reader(grader_file, delimiter=",")
    for line in lines:
      graders[line[0]] = (line[2],line[3])
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
  for question in questions:
    if question["Name"] in grading_assignments:
      graders = grading_assignments[question["Name"]]
      graded = question["Graded"]
      num_left = int(sub/(len(graders)))
      total_graded = 0
      remaining = {}
      for grader in graders:
        total_graded = 0
        remaining[grader] = num_left
        for counts in graded:
          ta = counts["Grader"]
          count = counts["Count"]
          total_graded += count
          if ta == grader:
            remaining[grader] = max(0,num_left - count)
        if total_graded >= sub:
          break
      if total_graded < sub:
        remaining = {key:val for key, val in remaining.items() if val != 0}
        finished[question["Name"]] = list(remaining.keys())
  return finished

# will need to integrade to google sheets
# return a question_name->[people to grade]
def getGradingAssigns(course,assignment):
  questions = {}
  return questions
  

# assume that you have a dictionary of question names -> [people to grade]
# call this grading_assignments
# convert into person->questions
def make_notify_list(remaining):
  toNotify = {}
  for question in remaining:
    for person in remaining[question]:
      if person in toNotify:
        toNotify[person].append(question)
      else:
        toNotify[person] = [question]
  return toNotify

## make the list of things to say to tell people
def notify(graders,notify_list):
  messages = {}
  for grader in notify_list:
    questions = notify_list[grader]
    if graders[grader][0] in messages:
      if graders[grader][1] in messages:
        messages[graders[grader][0]][graders[grader][1]].append("Don't forget to grade: " + ",".join(questions))
      else:
        messages[graders[grader][0]][graders[grader][1]] = [("Don't forget to grade: " + ",".join(questions))]
    else:
        messages[graders[grader][0]] = {graders[grader][1]:[("Don't forget to grade: " + ",".join(questions))]}
  return messages

# returns class->assignment->graderID->message_to_send
def send_notify(semester=None,graders=None):
  if semester == None:
    semester = loadSemester()
  if graders == None:
    graders = loadGraders()

  courses = getCourses(semester)
  assignments ={}
  messages = {}
  #course -> assign_name -> user-> [messages]
  for course in courses:
    assignments[course] = getAssignments(semester,course)
  for c in assignments:
    assigns = assignments[c]
    messages[c] = {}
    for a in assigns:
      grading_assigns = getGradingAssigns(c,a)
      questions,sub = getGrading(semester,c,a)
      if questions != None:
        remaining = getRemainingGrading(grading_assigns,questions,sub)
        notify_list = make_notify_list(remaining)
        message_dict = notify(graders,notify_list)
        for m in message_dict:
          messages[c][a] = message_dict[m]
        
  return messages 

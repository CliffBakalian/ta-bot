import math
import os

import csv
import json

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

# will need to integrade to google sheets
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
          #if a in messages[c]:
          messages[c][a] = message_dict[m]
          #else:
          #  messages[c] = {a:message_dict[m]}
        
  return messages 

print(send_notify())

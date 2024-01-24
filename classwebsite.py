import sqlite3
from utils import config, mk_oh_blocks

def get_discord_name(name):
  # BECAUSE I DON"T HAVE ANY OTHER WAY TO DO THIS FOR NOW
  fname = name.split(" ")[0]
  connection = sqlite3.connect(config["WEBSITE_DATABASE"])
  cursor = connection.cursor()
  get_user_id = "SELECT ID FROM auth_user where FIRST_NAME='"+fname+"'"
  cursor.execute(get_user_id)
  user_id = (cursor.fetchone())[0]

  get_discord_user_name = "SELECT DISCORD_NAME FROM courses_staff where USER_ID="+str(user_id)
  cursor.execute(get_discord_user_name)
  discord= (cursor.fetchone())[0]
  return discord

def get_tables():
  connection = sqlite3.connect(config["WEBSITE_DATABASE"])
  cursor = connection.cursor()
  sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
  cursor.execute(sql_query)
  print("List of tables\n")
   
  # printing all tables list
  print(cursor.fetchall())

def get_table(table,headers=False):
  connection = sqlite3.connect(config["WEBSITE_DATABASE"])
  cursor = connection.cursor()
  get_user_id = "SELECT * FROM "+table
  cursor.execute(get_user_id)
  print(cursor.fetchall())
  if headers:
    get_headers(cursor)

def get_courses_staff():
  connection = sqlite3.connect(config["WEBSITE_DATABASE"])
  cursor = connection.cursor()
  get_user_id = "SELECT * FROM courses_staff"
  cursor.execute(get_user_id)
  print(cursor.fetchall())
  get_headers(cursor)

def get_users():
  connection = sqlite3.connect(config["WEBSITE_DATABASE"])
  cursor = connection.cursor()
  get_user_id = "SELECT * FROM auth_user"
  cursor.execute(get_user_id)
  print(cursor.fetchall())
  get_headers(cursor)

def get_headers(cursor):
  names = [description[0] for description in cursor.description] 
  print(names)
  return names

def add_staff_member(directory_id,course_name):
  connection = sqlite3.connect(config["WEBSITE_DATABASE"])
  cursor = connection.cursor()

  get_user_id = "SELECT ID FROM auth_user where username='"+str(directory_id)+"'"
  cursor.execute(get_user_id)
  uid = (cursor.fetchone())[0]

  get_course_id = "SELECT ID FROM courses_course where course_name='"+str(course_name)+"'"
  cursor.execute(get_course_id)
  course_id = (cursor.fetchone())[0]
  get_table("courses_course")

  add_staff = "INSERT into courses_staff (user_id,course_id,role,picture,description) values("+str(uid)+","+str(course_id)+",'TA','','')"
  err = cursor.execute(add_staff)
  connection.commit()

'''
add office hours to db. inefficient but only run at the begining of the semester
'''
def add_office_hours(day,hour,end,course_name,ta_name):
  connection = sqlite3.connect(config["WEBSITE_DATABASE"])
  cursor = connection.cursor()

  get_user_id = "SELECT id FROM auth_user where first_name='"+str(ta_name.split(" ")[0])+"'"
  cursor.execute(get_user_id)
  try:
    uid = (cursor.fetchone())[0]
  except TypeError:
    print("could not find user: "+ ta_name+". Need to add user?")
    return

  get_staff_id = "SELECT id FROM courses_staff where user_id="+str(uid)
  cursor.execute(get_staff_id)
  try:
    staff_id= (cursor.fetchone())[0]
  except TypeError:
    print("could not find staff: "+ ta_name+". Need to add staff member?")
    return

  get_course_id = "SELECT ID FROM courses_course where course_name='"+str(course_name)+"'"
  cursor.execute(get_course_id)
  try:
    course_id = (cursor.fetchone())[0]
  except TypeError:
    print("could not find course: " + course_name)
    return
  get_table("courses_course")

  add_oh = "INSERT into courses_office_hours(ta_id,course_id,start,end,day,virtual) values("+str(staff_id)+","+str(course_id)+",'"+str(hour)+"','"+str(end)+"','"+str(day)+"',False)"
  cursor.execute(add_oh)
  connection.commit()

def synch_office_hours(course):
  blocks = (mk_oh_blocks(course))
  for block in blocks:
    try:
      day = block['day']
      start = block['start']
      end = block['end']
      name = block['name']
      add_office_hours(day,start,end,"Organization of Programming Languages",name)
    except:
      print(block)

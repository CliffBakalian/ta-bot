import json
from classwebsite import *
from sheets_parser import *
from utils import get_creds,mk_oh_blocks

'''
when setting up the course you need to add a few things to the class website
First you need to make the templates for office hours
after you make the template, head tas need to assign tas to slots
once tas are assigned, you need to load their office hours to the class website
'''

'''
make those tempaltes for us to fill out
'''
def make_templates(course):
  creds = get_creds()
  mk_OH_Template(course,creds)
  upload_graders(course,creds)

'''
once office hours sheet is populated, need to transfer it to class website
'''
def setup_office_hours(course):
  creds = get_creds()
  res = get_office_hours(course,creds) # write office hours to json
  blocks= mk_oh_blocks(course) 
  for block in blocks:
    day = block["day"]
    start = block["start"]
    end = block["end"]
    name = block["name"]
    add_office_hours(day,start,end,course,name)

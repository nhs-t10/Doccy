# Import statements
import json
import time
import re
from slackclient import SlackClient
import API_KEYS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import urllib.request
import os
import sys
import datetime

# Constants and Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
# Google Sheet credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name('doccy-215702-bd6ad5890442.json', scope)
# Google Sheets API Instance
gc = gspread.authorize(credentials)

sh = gc.create('Upcoming Robotics Events and Meetings 2018')
sh.share('nhsdoccy@gmail.com', perm_type='user', role='writer')
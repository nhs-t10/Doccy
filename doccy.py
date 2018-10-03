#!/usr/bin/env python3

# Import statements
import json
import time
import re
from slackclient import SlackClient
import API_KEYS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib.request
import datetime
import random
import heroku3
from datetime import timedelta

# Constants and Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
# Google Sheet credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name('doccy-215702-bd6ad5890442.json', scope)
# Google Sheets API Instance
gc = gspread.authorize(credentials)

# Slack Token (taken from python file for protection)
slack_token = API_KEYS.slack_token
slack_client = SlackClient(slack_token)

# Sheets instances

# Documentation Feed
docs = gc.open("Documentation Feed 2018").sheet1

# Registered Users
reg = gc.open("Registered").sheet1

#Scheduled Meeting Days
sched = gc.open("Upcoming Robotics Events and Meetings 2018").sheet1
days = sched.get_all_records()

# Heroku API Client
heroku_conn = heroku3.from_key('119be864-9d74-4722-803f-4e05a06da242')
app = heroku_conn.apps()['young-caverns-32300']

# more constants
SFTCMD = "#softwaredoc"
HRDCMD = "#hardwaredoc"
OUTCMD = "#outreachdoc"
OTHCMD = "#other"
HELLOCMD = "hello"
TESTCMD = "test"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
admin_phrases = ['check-who','get-latest','announce:']

#Boolean that is set for documentation vs conversationality. Assumes everything is documentation.
is_documentation = True

def send(msg, chn):
    '''
    Sends a message though a slack channel

    :param msg:
    :param chn:
    :return: None, send IM message to channel
    '''
    slack_client.api_call(
        "chat.postMessage",
        channel=chn,
        text=msg
)

def check_if_there(instance):
    '''
    Checks to see if a user is registered, or if a channel is identified.

    :param name or channel instance
    :return: boolean
    '''
    try:
        reg.find(instance)
        return True

    except:
        return False

def toJson(url):
    '''
    Turns any slack api call from url into json object

    :param url:
    :return: JSON Object from the resulting url
    '''
    obj = urllib.request.urlopen(url).read()
    json_obj = json.loads(obj.decode('utf-8'))
    return json_obj

# Function to parse bot commands
def parse_bot_commands(slack_events):
    '''
    Parses commands that the bot receives.
    :param slack_events:
    :return: message, channel ID
    '''
    for event in slack_events:
        # print(event)
        # If the event type is a message
        if event["type"] == "message" and not "subtype" in event:
            # Check to see if the channel is indeed a docbot channel, or if the text says
            # register.
            if MENTION_REGEX not in event['text']:
                message = event['text']
                return message, event["channel"], event['ts']
            # Check if someone mentions Doccy with @Doccy
            else:
                user_id, message = parse_direct_mention(event["text"])
                if user_id == doccybot_id:
                    print(message, event['ts'])
                    return message, event["channel"], event['ts']

    return None, None, None

def parse_direct_mention(message_text):
    '''
    Parses direct mentions with @

    :param message_text:
    :return: username, remaining message
    '''
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def convert_ts_to_date(ts, type):
    if type == "date":
        return datetime.datetime.fromtimestamp(int(float(ts))).strftime('%m/%d')
    elif type == "time":
        return datetime.datetime.fromtimestamp(int(float(ts))).strftime('%H-%M-%S')
    elif type == "day":
        return datetime.datetime.fromtimestamp(int(float(ts))).strftime('%d')
    elif type == "minute":
        return datetime.datetime.fromtimestamp(int(float(ts))).strftime('%M')

def handle_documentation(command, channel, user, time):
    '''
    Handles commands from the user, provides different responses based on the name

    :param command:
    :param channel:
    :param user:
    :return: Sends message to user via Bot
    '''
    # Default response
    response = "Sorry, I didn't detect a documentation tag. Please add #softwaredoc, " \
               "#hardwaredoc, #outreachdoc or #other to the end of your message."
    # Checks to make sure if the user is registered, or if they are registering.

    # Get current date from ts object
    date = convert_ts_to_date(time, "date")

    if check_if_there(user):
        # If statements are similar, they add to a cell depending on what is being documented.
        if command.startswith(HELLOCMD):
            response = "Why hello!"
        elif command.endswith(TESTCMD):
            response = "Hello there, {}.".format(user)
        else:
            response = "Thanks for documenting, {}!".format(user)
            if '-c ' in command:
                public_message = command.split("-c ")[0] + " -" + user
                new_row = [command.split('-c ')[1], public_message, date]
            else:
                public_message = command + " -" + user
                new_row = ['Other', public_message,date]
            docs.append_row(new_row)

        # Sends the response back to the channel
        send(response, channel)

    else:
        send("You haven't registered yet! To do so, please type 'register'.", channel)

def annoy_all():
    '''
    We will check who needs to document by looking through doccy's im list.
    For each conversation in that list, we will get the chat ID and look through its history.
    If the timestamp of the last sent message is more than two days old, then remind the
    user to document, by sending a message through that user's channel. We can also
    check to see if the last sent message says "Thanks for documenting", because then
    we will know if the person's last sent message was documentation.

    :return: None, sends IM's to all of doccy's im channels.
    '''
    doccy_list = toJson("https://slack.com/api/im.list?token="+slack_token+"&pretty=1")
    im_list = doccy_list['ims']
    for i in im_list:
        im_hist = toJson(
            "https://slack.com/api/im.history?token="+slack_token+"&channel=" + i['id']
            + "&pretty=1")
        try:
            if(check_if_there(i['id'])):
                if int(convert_ts_to_date(time.time(), "day")) - int(
                        convert_ts_to_date(im_hist['messages'][0]['ts'], "day")) >= 2:
                    send("Sorry, it looks like you haven't documented in the last two days. "
                         "Tell me what you did during the last meeting!",
                         i['id'])
                elif int(convert_ts_to_date(time.time(), "day")) - int(
                        convert_ts_to_date(im_hist['messages'][0]['ts'], "day")) == 0:
                    send("Thank you for documenting today!",
                         i['id'])
                elif int(convert_ts_to_date(time.time(), "day")) - int(
                        convert_ts_to_date(im_hist['messages'][0]['ts'], "day")) == 1:
                    send("It looks like you documented yesterday, but tell me more about what you did today!",
                         i['id'])
        except IndexError:
            send("It looks like you haven't spoken to me in a while, which means you haven't "
                 "documented either. "
                 "Pleasure to meet you! Tell me what you did during our last meeting!",
                 i['id'])

def announce(msg):
    '''
    Announces something from Doccy into a channel on slack
    :return: None
    '''
    string = '@here {}'.format(msg)
    send(string,'#t-10')

def id_to_name(id):
    with open('members.txt') as mem_list:
        listopeep = json.load(mem_list)
        for i in listopeep['members']:
            if i['id'] == id:
                return i['profile']['real_name']

def restart():
    '''
    Restart's Doccy, should he be need it
    :return:
    '''
    app.restart()


def handle_convo(text,channel,user):
    '''
    Takes input of a conversation, returns a response
    :param text:
    :return: None, response
    '''
    response = 'foo bar'
    greetings = ['hello','hi','sup','hey']
    goodbyes = ['bye','peace','latah','adios']
    swears = ['fuck', 'piss', 'shit', 'cunt', 'ass', 'crap']
    thanks = ['thanks!','thank you!','ty','thanks']
    question_responses = ['Sorry, I\'m just a robot. You should ask Mr. Batra about that.',
                          'Ask Davis, he\'s your project manager!', 'No.','Yes','Of course!',
                          'Ask Shaashwat!']
    random_responses = ['Oh, that\'s pretty neat!','What was that?','Ok, cool.','Beep boop.']
    text = text.lower()
    if check_if_there(user):
        if text == admin_phrases[0]:
            people = []
            doccy_list = toJson("https://slack.com/api/im.list?token=" + slack_token + "&pretty=1")
            im_list = doccy_list['ims']
            for i in im_list:
                im_hist = toJson(
                    "https://slack.com/api/im.history?token=" + slack_token + "&channel=" + i['id']
                    + "&pretty=1")
                if(check_if_there(i['id'])):
                    if(int(convert_ts_to_date(time.time(), "day")) - int(
                            convert_ts_to_date(im_hist['messages'][0]['ts'], "day")) == 0):
                        print(id_to_name(i['id']))
                        people.append(id_to_name(i['id']))
            response = "The following people have documented: {}".format(",".join(people))
        elif text == admin_phrases[1]:
            index = docs.row_count
            row = docs.row_values(index)
            response = "The last documentation was \"{}\" on {}".format(row[1],row[2])
        elif admin_phrases[2] in text:
            message = (text.split(': ')[1]).split('-nd')[0]
            announce(message)
            response = "I sent {} to #general!".format(message)
        elif any(match in text for match in greetings):
            response = 'Oh, hey there {}'.format(user)
        elif any(match in text for match in goodbyes):
            response = 'See you later, {}'.format(user)
        elif any(match in text for match in swears):
            response = 'Hey, no need to use that kind of language!'
        elif any(match in text for match in thanks):
            response = 'You\'re welcome, {}'.format(user)
        elif 'flip a coin' in text:
            response = "The coin came up {}!".format(random.choice(['heads','tails']))
        elif '?' in text:
            response = random.choice(question_responses)
        elif text == 'restart':
            restart()
        else:
            response = random.choice(random_responses)
    elif 'register' in text:
        if check_if_there(user):
            response = "You're already registered! Get documenting!"
        else:
            new_line = [user, channel]
            reg.append_row(new_line)
            response = "Thank you for registering, {}!".format(user)
    else:
        response = 'You aren\'t registered yet! To register, please type \'register\'.'
    send(response,channel)

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Doccy Bot connected and running!")
        print('Current time: {}'.format(convert_ts_to_date(time.time(),'time')))
        print('All systems go!')
        doccybot_id = slack_client.api_call("auth.test")["user_id"]
        curruser_id = "member"
        with open('members.txt') as members:
            data = json.load(members)
            while True:
                events = slack_client.rtm_read()
                command, channel, currtime = parse_bot_commands(events)
                if command:
                    curruser_id = events[0]['user']
                    for i in data['members']:
                        if i['id'] == curruser_id:
                            currname = i['profile']['real_name']
                            if len(command) < 40 or '-nd' in command:
                                handle_convo(command, channel, currname)
                                print(currname, "said", command[:20] + "...", "in", channel)
                            else:
                                handle_documentation(command, channel, currname, currtime)
                                print(currname, "said", command[:20] + "...", "in", channel)
                # If it is 8:00 on any given day (doccy is 4 hours ahead)
                if convert_ts_to_date(time.time(), "time") == "23-50-00":
                    print("It's time!")
                    # If it is a meeting date, then check who needs to document.
                    for i in range(0, len(days)):
                        if convert_ts_to_date(time.time(), "date") == days[i]["Date"] and \
                                        days[i]['Event'] == "Meeting":
                            print(convert_ts_to_date(time.time(), "date"),"is a meeting day!")
                            try:
                                annoy_all()
                                print("I annoyed people today!")
                            except Exception as e:
                                print("I tried to annoy people, but I encountered {}".format(e))
                # Wait one second between all event handling
                time.sleep(1)
    else:
        print("Connection failed.")
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import errors
from test import get_credentials
from datetime import datetime, timedelta
import httplib2
import os
import email
import base64
import unicodedata
import sys
import unicodedata
import string

# gmail parameters
msg_label = '<gmail_label>'
my_email = '<email>'

# file settings
input_file = 'messageids.txt'

# ----------------------------------------------------------------------
# Update the days of the week if the time has passed 17:00 (配信時間)
# ----------------------------------------------------------------------
def updateDays(today):
    time_now = datetime.now().strftime('%H:%M')
    update_time = '17:00'
    if time_now >= update_time:
        today = today + timedelta(days=1)
        return today
    else:
        print("notifications not sent yet")

# ----------------------------------------------------------------------
# Every message body contains data from the following carriers:
#   carrier #1
#   carrier #2
#   carrier #3
# Each division means we count the total extracted nos together representing each day
# ----------------------------------------------------------------------
def SortByCarriers(counter, access_count, week_counter):
    if counter % 3 == 0:
        return True
    else:
        return False

# ----------------------------------------------------------------------
# Fetch the integers from all Japanese letters
# ----------------------------------------------------------------------
def ExtractInt(message_body):
    normalized_nos = unicodedata.normalize('NFKD', message_body).encode('ASCII', 'ignore')
    extracted_nos = [int(s) for s in normalized_nos.split() if s.isdigit()]
    return sum(extracted_nos)

# ----------------------------------------------------------------------
# Get messages from inbox
# ----------------------------------------------------------------------
def GetMessages(service, user_id, today, week_counter):
    try:
        message_ids = open(input_file).readlines()
        msg_body_list = []
        for i in range(len(message_ids)):
            message = service.users().messages().get(  userId=user_id,
                                                       id=message_ids[i].rstrip(),
                                                       format='raw').execute()

            msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
            mime_msg = email.message_from_string(msg_str)
            message_body = unicode(mime_msg.get_payload(), 'shift-jis')
            extracted_int = int(ExtractInt(message_body))
            msg_body_list.append(extracted_int)
            print(msg_body_list)
            if (SortByCarriers(i + 1,  sum(msg_body_list), week_counter) == True):
                week_counter += 1
                recorded_date = today - timedelta(days=week_counter)
                print("----------------------------- total count [ ", sum(msg_body_list) ," ] date = ", recorded_date.strftime('%Y/%m/%d'))
                del msg_body_list[:]

    except errors.HttpError, error:
        print('An error occurred: %s' % error)

# ----------------------------------------------------------------------
# Get all message ids based on label
# ----------------------------------------------------------------------
def GetMessageIds(today, last_week, service, user_id, msg_label):
    try:
        query = "before: {0} after: {1}".format(today.strftime('%Y/%m/%d'),
                                                last_week.strftime('%Y/%m/%d'))

        response = service.users().messages().list( userId=user_id,
                                                    labelIds=msg_label,
                                                    q=query).execute()
        msg_id_file = open(input_file, 'w')
        for i in range(len(response['messages'])):
            msg_id_file.write(response['messages'][i]['id'] + '\n')

    except errors.HttpError, error:
        print('An error occurred: %s' % error)

# ----------------------------------------------------------------------
# Main program
# Calculates all access count in descending order, starting from recent to old (bottom to top)
# ----------------------------------------------------------------------
def main():
    # date settings
    today = datetime.now()
    last_week = today - timedelta(days=7)

    # print this just in case
    print("Today     : ", today)
    print("Last week : ", last_week, '\n')

    # week counter
    week_counter = 0
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    results = service.users().labels().list(userId=my_email).execute()

    # check if we need to update the days of the week before calculating access logs
    today = updateDays(datetime.now())

    GetMessageIds(today, last_week, service, my_email, msg_label)
    GetMessages(service, my_email, today, week_counter)

if __name__ == '__main__':
    main()

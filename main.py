# -*- coding:utf-8 -*-
from datetime import datetime, timedelta
import time

import re
from apscheduler.scheduler import Scheduler
import sensitive.sensitive_data as sensitive_data
import vk_api
import feedparser
from pymongo import Connection


reposts = [{'rss': 'http://zadolba.li/rss/', 'public_id': 66035937},
           {'rss': 'http://ithappens.ru/rss', 'public_id': 66038423},
           {'rss': 'http://bash.im/rss/', 'public_id': 65977822},
           {'rss': 'http://killmeplz.ru/rss/', 'public_id': 66094736}]

"""
cc_ShRISnwTRjlD is a MongoDB database name
"""
db = Connection(sensitive_data.mongodb_uri).cc_ShRISnwTRjlD
# db = Connection('localhost:27017').cc_ShRISnwTRjlD  # for Debugging in local DB

while True:
    vk = vk_api.VkApi(sensitive_data.vk_login, sensitive_data.vk_pass, app_id=sensitive_data.vk_app_id, scope=73728,
                      number=sensitive_data.vk_telephone)
    if vk.check_token():
        break
    else:
        time.sleep(60)



# u can modify it for configuring every rss feed
def inspect_entry_text(entry, from_rss):
    attachments = None
    entry['summary'] = entry['summary'].replace("<br />", "\n").replace("&gt;", ">").replace("&lt;", "<").replace(
        "&quot;", '"')
    entry['summary'] = re.sub('<[^<]+?>', '', entry['summary'])
    if from_rss == 'http://zadolba.li/rss/' or from_rss == 'http://ithappens.ru/rss':
        message = entry['title_detail']['value'] + '\n\n' + entry['summary']
    else:
        message = entry['summary']
    return {'message': message, 'attachments': attachments}


# Don't modify this
def parser():
    print 'parser!'
    global reposts
    for item in reposts:
        parsed_rss = feedparser.parse(item['rss'])
        for entry in parsed_rss['entries'][0:8]:  # last 8 rss entries
            if db[str(item['public_id'])].find({'id': entry['id']}).count() == 0:
                entry_for_vk = inspect_entry_text(entry, item['rss'])  # отправляем текст на обработку
                db[str(item['public_id'])].insert({'id': entry['id']})  # запоминаем, что уже обрабатывали запись
                db['queue'].insert({"public_id": item["public_id"], 'message': entry_for_vk['message'],
                                    'attachments': entry_for_vk['attachments']})  # в очередь


def post_to_vk(public, message, attachments):
    vk.method('wall.post', {'owner_id': -int(public), 'from_group': 1, 'message': message, 'attachments': attachments})


def poster():
    print 'poster!'
    while db['queue'].find().count() > 0:
        to_post = [x for x in db['queue'].find(sort=[("_id", -1)])]
        post_to_vk(to_post[0]['public_id'], to_post[0]['message'], to_post[0]['attachments'])
        db['queue'].remove({'_id': to_post[0]['_id']})
        time.sleep(11)  # waiting for posting without captcha


def clean_old():
    print 'cleaner!'
    for item in reposts:
        cur_public = str(item['public_id'])
        while db[cur_public].find().count() > 300:  # saving 300 latest entries
            db[cur_public].remove({'_id': to_post[0]['_id']})

sched = Scheduler()
start_date = datetime.now() + timedelta(seconds=80)
sched.add_interval_job(parser, seconds=100, start_date=start_date)
sched.add_interval_job(poster, seconds=100)
sched.add_interval_job(clean_old, days=1, start_date=start_date)
sched.standalone = True
sched.start()

import datetime
import json
import logging
import os
import re
from keyword import iskeyword

import requests
from flask import jsonify
from flask_apscheduler import APScheduler
from isodate import parse_datetime

from models import AddressList, Rule, RuleResult


def method_runnert(a, b):
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Running')
    scan_rule_list()


class RunnerConfig(object):  # 创建配置，用类
    JOBS = [{
        'id': 'job2',
        'func': method_runnert,  # 方法名
        'args': (1, 2),  # 入参
        'trigger': 'interval',  # interval表示循环任务
        'seconds': 125  # 每隔125秒执行一次,
    }]


def runner_start(app):
    app.config.from_object(RunnerConfig())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()


# ===============================================
def find_string_withend(text, end_str):
    i = text.find(end_str)
    if i == -1:
        return ''
    return text[:i]


def find_string_withstart(text, start_str):
    i = text.find(start_str)
    if i == -1:
        return ''
    return text[i:]


def pick_ckb_address(text):
    start = find_string_withstart(text, 'ckb')
    if (len(start) > 0):
        str = ["\n", "\r", "\t", " ", ","]
        for s in str:
            pos = start.find(s)
            if pos != -1:
                return start[:pos]
        return (start)


# 跳过finished检查,直接执行rule
def run_refresh_rule(rule):
    try:
        if(rule.action.type != 'discussion'):
            logging.error("rule {}-{} is not discussion".format(rule.id, rule.name))
            return False
        
        isNervos = False
        keyword=None
        act = json.loads(rule.action.to_json())
        for condition in act['condition']:
            
            if('with'in condition and condition['of'].lower() =='nervos' and condition['with'].lower() =='address'):
                isNervos = True
                continue
            if('with' in condition and condition['with'].lower() =='keyword'):
                keyword = condition['of']
        
        if(isNervos):
            rule.update(finished=True)
            addresses, success = run_github_discussions_ckb(rule.action,keyword)
            if success:
                list = AddressList.objects.create(
                    result_id='1', list=addresses)
                r = RuleResult.objects.create(rule_id=str(
                    rule.id), rule_name=rule.name, rule_creator=rule.creator, address_list_id=str(list.id))
                list.update(result_id=str(r.id))
                return True
            else:
                logging.error("rull {}-{} runner fail".format(rule.id, rule.name))
                return False
        else:
            logging.error("rull unsupport")
            return False
    except Exception as e:
        logging.error(e)
        rule.update(finished=False)
        return False

# 检查是否在时间范围内且到结束日期当日（精确到‘日’）


def is_to_time(rule):
    try:
        # 2022-03-28T03:34:24.467Z
        start_date = parse_datetime(rule.action.start_time)
        start_date = start_date.date()

        end_date = parse_datetime(rule.action.end_time)
        #end_date = parse_datetime('2022-04-21T03:34:24.467Z')
        end_date = end_date.date()

        now = datetime.datetime.now().date()
        if start_date <= now <= end_date and now == end_date:
            return True
        else:
            return False
    except Exception as e:
        logging.error(e)
        return False


def scan_rule_list():
    # 未添加时间及类型检查
    rules = Rule.objects(finished=False)
    for rule in rules:
        if is_to_time(rule) == False:
            logging.info(
                "rule {}-{} is not to time".format(rule.id, rule.name))
            continue
        rule.finished = True
        rule.save()
        run_refresh_rule(rule)


def post_github_graphql(input):
    query = """query{
        repository(owner: \"""" + input[0] + "\", name: \"" + input[1] + """\") {
            discussion(number: """ + input[3] + """) {
            comments(first: 100) {
                edges {
                node {
                    bodyText
                }
                }
            }
            }
        }
        }"""

    headers = {'Content-Type': 'application/json',
               'Authorization': 'bearer ' + str(os.environ.get("GITHUB_GRAPHQL_APIKEY"))}
    request = requests.post('https://api.github.com/graphql',
                            json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json(), 0
    else:
        logging.error("Query failed to run by returning code of {}. {}\n{}".format(
            request.status_code, request.reason, query))
        return None, -1

def run_github_discussions_ckb(action,keyword):
    # 'https://github.com/rebase-network/hello-world/discussions/8'
    try:
        github_host = 'https://github.com/'
        github = action.url.find(github_host)
        if (github == -1):
            logging.error('no github url')
            return None, False
        url = action.url[github + len(github_host):]
        input = url.split('/')
        print("url:", input)
        #action check
        if(len(input) != 4):
            logging.error('url format error, url: {}'.format(url))
            return None, False
        if(action.type !='discussion' or input[2] != 'discussions'):
            logging.error('url format error, not discussions')
            return None, False
        if(input[3] == ''):
            logging.error('url format error, no number')
            return None, False
        
        if (len(input) != 4 or input[2] != 'discussions'):
            logging.error('url format error')
            return None, False
        
        result, err = post_github_graphql(input)  # Execute the query
        if err == -1:
            logging.error(
                "Query failed to run by returning code of {}. {}".format(err, result))
            return None, False
        remaining_rate_limit = result["data"]["repository"]["discussion"]['comments']['edges']

        addresses = []
        for (i, comment) in enumerate(remaining_rate_limit):
            bodyText = comment['node']['bodyText']
            if(keyword != None ):
                k = re.search(keyword, bodyText, re.IGNORECASE)
                if(k == None):
                    continue
            address = pick_ckb_address(bodyText)
            if address is not None:
                print("Found address: {}".format(address))
                addresses.append(address)
                
        if len(addresses) == 0:
            print("No address found")
            return None, False
        return addresses, True
    except Exception as e:
        logging.error(e)
        return None, False

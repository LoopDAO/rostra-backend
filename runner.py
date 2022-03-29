import datetime
from pprint import pprint
from bson.objectid import ObjectId
from flask import Flask, abort, jsonify, make_response
from flask_apscheduler import APScheduler
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_restx import Api, Resource, fields

from models import Guild, Rule, RunResult
from rsa_verify import flashsigner_verify


def method_runnert(a, b):
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Running')


class RunnerConfig(object):  # 创建配置，用类
    JOBS = [{
        'id': 'job2',
        'func': method_runnert,  # 方法名
        'args': (1, 2),  # 入参
        'trigger': 'interval',  # interval表示循环任务
        'seconds': 25  # 每隔25秒执行一次,
    }]


def runner_start(app):
    app.config.from_object(RunnerConfig())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
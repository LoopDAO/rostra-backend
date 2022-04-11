import datetime
import json
import logging
import os
import uuid
from email import message
from mimetypes import init
from pprint import pprint
from telnetlib import PRAGMA_HEARTBEAT

from black import err
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_restx import Api, Resource, fields
from github import Github

from github_graphql import post_github_graphql_commits
from github_pygithub import get_github_repo_commits, get_github_repo_stars
from models import AddressList, Guild, Nft, Rule, RuleResult
from rsa_verify import flashsigner_verify
from runner import run_refresh_rule, runner_start

app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {'db': 'guild', 'host': 'localhost', 'port': 27017}

db = MongoEngine()
db.init_app(app)
api = Api(app, version='1.0', title='Rostra Backend API', description='Rostra Backend Restful API')
rostra_conf = api.namespace('', description='Rostra APIs')

load_dotenv()

runner_start(app)

CORS(app)

app.url_map.strict_slashes = False


@rostra_conf.route('/guild/get/', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class Get(Resource):

    def get(self):
        guilds = Guild.objects()
        return jsonify({"result": guilds})


@rostra_conf.route('/guild/<guild_id>', methods=['GET'])
@rostra_conf.doc(params={'guild_id': 'guild id'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class Get(Resource):

    def get(self, guild_id):
        try:
            query_by_guild_id = Guild.objects(guild_id=guild_id)
            print(query_by_guild_id)
            if query_by_guild_id is not None and len(query_by_guild_id) != 0:
                return jsonify({"result": query_by_guild_id[0]})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e)}


@rostra_conf.route('/guild/get/<ipfsAddr>', methods=['GET'])
@rostra_conf.doc(params={'ipfsAddr': 'ipfs addr'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class Get(Resource):

    def get(self, ipfsAddr):
        try:
            query_by_ipfsAddr = Guild.objects(ipfsAddr=ipfsAddr)
            print(query_by_ipfsAddr)
            if query_by_ipfsAddr is not None and len(query_by_ipfsAddr) != 0:
                return jsonify({"result": query_by_ipfsAddr})
            else:
                return {"result": []}, 200
        except Exception as e:
            return {'error': str(e)}


resource_fields = rostra_conf.model(
    'guild', {
        'name': fields.String(required=True, description='The guild name identifier'),
        "desc": fields.String,
        "creator": fields.String,
        "ipfsAddr": fields.String(required=True, description='The ipfs address of the guild'),
        "signature": fields.String(requerd=True, description='The signature of the guild'),
    })


@rostra_conf.route('/guild/add/', methods=['POST'])
class Add(Resource):

    @rostra_conf.doc(body=resource_fields, responses={201: 'Guild Created'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        data = api.payload
        guildInfo = {"name": data["name"], "desc": data["desc"], "creator": data["creator"], "ipfsAddr": data["ipfsAddr"]},

        signature = data['signature']

        # validation if the guild name already exists
        if len(Guild.objects(name=data['name'])) != 0:
            return {'message': 'The Guild Name Already Exists! Please change your guild name'}, 401
        # validation signature
        if len(signature) == 0:
            return {'message': 'The signature is empty'}, 401

        message = json.dumps(guildInfo, separators=(',', ':'))
        if len(message) > 2:
            message = message[1:-1]
        result = flashsigner_verify(message=message, signature=signature)
        if result == False:
            return {'message': 'The signature is error'}, 401
        guild = Guild(guild_id=str(uuid.uuid4()),
                      name=data['name'],
                      desc=data['desc'],
                      creator=data['creator'],
                      ipfsAddr=data['ipfsAddr'],
                      signature=signature)
        guild.save()
        return {'message': 'SUCCESS'}, 201


@rostra_conf.route('/guild/delete/<guild_id>', methods=['DELETE'])
@rostra_conf.doc(params={'guild_id': 'Id of the guild'})
class Delete(Resource):

    @api.response(201, 'Guild Deleted')
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def delete(self, guild_id):
        try:
            query_by_guild_id = Guild.objects(guild_id=guild_id)
            print(query_by_guild_id)

            if query_by_guild_id is not None and len(query_by_guild_id) != 0:
                query_by_guild_id.delete()
                return {'message': 'SUCCESS'}, 201
            else:
                return {"messgae": 'The Guild Id cannot be found'}, 401

        except Exception as e:
            return {'error': str(e)}


# nft
nft_model = rostra_conf.model(
    'nft', {
        'name': fields.String(required=True, description='The nft name'),
        "desc": fields.String,
        "image": fields.String(required=True, description='The image url of nft'),
        "cota_id": fields.String(required=True, description='The cota id of the nft'),
        "type": fields.Integer(required=True, description='The type of the nft, 1 - nft, 2- ticket')
    })


@rostra_conf.route('/nft/add/', methods=['POST'])
class Add(Resource):

    @rostra_conf.doc(body=nft_model, responses={201: 'NFT Created'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            print(data)
            # validation if the nft name already exists
            if len(Nft.objects(name=data['name'])) != 0:
                return ResponseInfo(401, 'The NFT Name Already Exists! Please change your nft name')

            cotaId = data['cota_id']

            # validation if the nft cota id already exists
            if len(Guild.objects(name=cotaId)) != 0:
                return {'message': 'The Cota ID Already Exists! Cota ID should be only to one nft! Please Check!'}, 401

            if len(cotaId) != 42:
                return {'message': 'The Cota ID should be of length 42!'}, 401

            if not cotaId.startswith('0x'):
                return {'message': 'The Cota ID should start with 0x!'}, 401

            nft = Nft(name=data['name'], desc=data['desc'], image=data['image'], cota_id=data['cota_id'], type=data['type'])
            nft.save()
            return {'message': 'SUCCESS'}, 201
        except Exception as e:
            return {'error': str(e)}, 500


@rostra_conf.route('/nft/get/', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class Get(Resource):

    def get(self):
        nfts = Nft.objects(type=1)
        return jsonify({"result": nfts})


@rostra_conf.route('/nft/get/<cotaId>', methods=['GET'])
@rostra_conf.doc(params={'cotaId': 'cota id of the nft'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class Get(Resource):

    def get(self, cotaId):
        try:
            query_by_cotaId = Nft.objects(cota_id=cotaId)
            print(query_by_cotaId)
            if query_by_cotaId is not None and len(query_by_cotaId) != 0:
                return jsonify({"result": query_by_cotaId})
            else:
                return {"result": []}, 200
        except Exception as e:
            return {'error': str(e)}


@rostra_conf.route('/ticket/get/', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class Get(Resource):

    def get(self):
        tickets = Nft.objects(type=2)
        return jsonify({"result": tickets})


# ==========================================================
# rule start
rule_fields = rostra_conf.model(
    'rule', {
        'name': fields.String(required=True, description='The rule name identifier'),
        "desc": fields.String,
        "creator": fields.String,
        "ipfsAddr": fields.String(required=True, description='The ipfs address of the rule'),
        "signature": fields.String(requerd=True, description='The signature of the rule'),
        "action": fields.List(fields.String, required=True, description='The action info of the rule'),
        "nft": fields.List(fields.String, required=True, description='The nft info of the rule'),
    })


@rostra_conf.route('/rule/add/', methods=['POST'])
class RuleAdd(Resource):

    @rostra_conf.doc(body=rule_fields, responses={201: 'Rule Created'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            print(data)
            ruleInfo = {
                "name": data["name"],
                "desc": data["desc"],
                "creator": data["creator"],
                "action": data["action"],
                "nft": data["nft"]
            },

            signature = data['signature']

            # validation if the rule name already exists
            if len(Rule.objects(name=data['name'])) != 0:
                return ResponseInfo(401, 'The Rule Name Already Exists! Please change your rule name')
            # validation signature
            if len(signature) == 0:
                return ResponseInfo(401, 'The signature is empty')

            message = json.dumps(ruleInfo, separators=(',', ':'))
            if len(message) > 2:
                message = message[1:-1]
            # result = flashsigner_verify(message=message, signature=signature)
            # if result == False:
            #     return {'message': 'The signature is error'}, 401
            rule = Rule(name=data['name'],
                        desc=data['desc'],
                        creator=data['creator'],
                        signature=signature,
                        action=data['action'],
                        nft=data['nft'],
                        finished=False)

            rule.save()
            return {'rule_id': str(rule['id'])}, 201
        except Exception as e:
            logging.error(e)
            return {'error': str(e)}, 500


@rostra_conf.route('/rule/get/', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RuleGetAll(Resource):

    def get(self):
        try:
            query_by_rule_id = Rule.objects()
            if query_by_rule_id is not None and len(query_by_rule_id) != 0:
                return jsonify({"result": query_by_rule_id})
            else:
                return {"result": []}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}


@rostra_conf.route('/rule/<rule_id>', methods=['GET'])
@rostra_conf.doc(params={'rule_id': 'rule id'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RuleGet(Resource):

    def get(self, rule_id):
        try:
            query_by_rule_id = Rule.objects(id=rule_id)
            print(query_by_rule_id)
            if query_by_rule_id is not None and len(query_by_rule_id) != 0:
                return jsonify({"result": query_by_rule_id[0]})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/rule/walletaddr/<wallet_addr>', methods=['GET'])
@rostra_conf.doc(params={'wallet_addr': 'wallet_addr id'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RuleGetByWallet(Resource):

    def get(self, wallet_addr):
        try:
            query = Rule.objects(creator=wallet_addr)
            print(query)
            if query is not None and len(query) != 0:
                return jsonify({"result": query})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


# rule end
# ==========================================================
# Runner start
runresult_fields = rostra_conf.model(
    'runresult', {
        'rule_name': fields.String(required=True, description='The rule name identifier'),
        "rule_creator": fields.String,
        'rule_creator': fields.String,
        'result': fields.List(fields.String),
    })


@rostra_conf.route('/result/add', methods=['POST'])
class RunresultAdd(Resource):

    @rostra_conf.doc(body=runresult_fields, responses={201: 'RunResult Created'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            print(data)

            if len(RuleResult.objects(rule_id=data['rule_id'])) != 0:
                return ResponseInfo(401, 'The RunResult Already Exists! ')

            runresult = RuleResult(rule_id=data['rule_id'], result=data['result'])
            runresult.save()
            return {'id': str(runresult['id']), 'rule_id': runresult['rule_id']}, 201
        except Exception as e:
            return {'error': str(e)}, 500


@rostra_conf.route('/result/refresh/<rule_id>', methods=['GET'])
class RunresultRefreshByRuleIDGET(Resource):

    @rostra_conf.doc(params={'rule_id': 'rule_id'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def get(self, rule_id):
        try:
            rule = Rule.objects(id=rule_id)
            success = run_refresh_rule(rule[0])
            if success:
                return ResponseInfo(200, 'RuleRunresultRefresh success')
            else:
                return ResponseInfo(401, 'RuleRunresultRefresh failed')
        except Exception as e:
            return {'error': str(e)}, 500


@rostra_conf.route('/result/refresh/', methods=['POST'])
class RunresultRefreshByRuleID(Resource):

    @rostra_conf.doc(params={'rule_id': 'rule_id'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            print("/result/refresh/", data['rule_id'])
            rule = Rule.objects(id=data['rule_id'])
            success = run_refresh_rule(rule[0])
            if success:
                return {'message': 'RuleRunresultRefresh success'}, 201
            else:
                return {'message': 'fail'}, 401
        except Exception as e:
            return {'error': str(e)}, 500


@rostra_conf.route('/result/<id>', methods=['GET'])
@rostra_conf.doc(params={'id': 'id'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultGetByID(Resource):

    def get(self, id):
        try:
            query_by_runresult_id = RuleResult.objects(id=id)
            if query_by_runresult_id is not None and len(query_by_runresult_id) != 0:
                return jsonify({"result": query_by_runresult_id[0]})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/result/get/walletaddr/<wallet_addr>', methods=['GET'])
@rostra_conf.doc(params={'wallet_addr': 'wallet_addr'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultGetByWallet(Resource):

    def get(self, wallet_addr):
        try:
            query = RuleResult.objects(rule_creator=wallet_addr)
            if query is not None and len(query) != 0:
                return jsonify({"result": query})
            else:
                return {"result": ''}, 200
        except Exception as e:
            logging.error(e)
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/address_list/<id>', methods=['GET'])
@rostra_conf.doc(params={'id': 'id'})
@rostra_conf.doc(params={'page,per_page': '?page=1&per_page=10'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class GetAddressList(Resource):

    def get(self, id):
        try:
            query = AddressList.objects(id=id)
            count = len(query[0].list)
            if query is not None and count != 0:
                page = int(request.args.get('page', 1))  # 当前在第几页
                page = 1 if page < 1 else page

                per_page = int(request.args.get('per_page', 3))  # 每页几条数据
                per_page = 10 if per_page < 1 else per_page

                if count % per_page > 0:
                    total_page = int(count / per_page + 1)
                else:
                    total_page = int(count / per_page)
                if (page > total_page):
                    return {"result": ''}, 200
                return jsonify(query[0].list[(page - 1) * per_page:page * per_page])

            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/address_list/result_id/<result_id>', methods=['GET'])
@rostra_conf.doc(params={'result_id': 'result_id'})
@rostra_conf.doc(params={'page,per_page': '?page=1&per_page=10'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class GetAddressList(Resource):

    def get(self, result_id):
        try:
            query = AddressList.objects(result_id=result_id)
            count = len(query[0].list)
            if query is not None and count != 0:
                page = int(request.args.get('page', 1))  # 当前在第几页
                page = 1 if page < 1 else page

                per_page = int(request.args.get('per_page', 3))  # 每页几条数据
                per_page = 10 if per_page < 1 else per_page

                if count % per_page > 0:
                    total_page = int(count / per_page + 1)
                else:
                    total_page = int(count / per_page)
                if (page > total_page):
                    return {"result": ''}, 200
                return jsonify(query[0].list[(page - 1) * per_page:page * per_page])

            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/address_list/get/', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class GetAddressList(Resource):

    def get(self):
        try:
            query = AddressList.objects()
            if query is not None:
                return jsonify(query)

            else:
                return {"result": ''}, 200
        except Exception as e:
            logging.error(e)
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/result/ruleid/<rule_id>', methods=['GET'])
@rostra_conf.doc(params={'rule_id': 'rule_id'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultRuleidGet(Resource):

    def get(self, rule_id):
        try:
            query_by_rule_id = RuleResult.objects(rule_id=rule_id)
            if query_by_rule_id is not None and len(query_by_rule_id) != 0:
                return jsonify({"result": query_by_rule_id[0]})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/result/get', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultGetAll(Resource):

    def get(self):
        try:
            query = RuleResult.objects()
            if query is not None and len(query) != 0:
                return jsonify({"result": query})
            else:
                return {"result": []}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}


@rostra_conf.route('/result/delete', methods=['POST'])
@rostra_conf.doc(params={'rule_id': 'Id of the rule', 'address': 'address of runner result'})
class RunresultDelete(Resource):

    @api.response(201, 'Address Deleted')
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            rule_id = data['rule_id']
            address = data['address']

            query = RuleResult.objects(rule_id=rule_id)

            if query is not None and len(query) != 0:
                id = query[0].address_list_id
                query2 = AddressList.objects(id=id)
                if query2 is not None:
                    address_list = jsonify(query2[0]['list']).json  # query2[0].list
                    if address in address_list:
                        address_list.remove(address)

                        query2.update_one(list=address_list)
                        return ResponseInfo(201, 'Address:{} Deleted success!'.format(address))
                    else:
                        return ResponseInfo(401, 'Address:{} not in list'.format(address))
            else:
                return {"error": 'The Result cannot be found'}, 401

        except Exception as e:
            logging.error(e)
            return {'error': str(e)}, 500
# Runner end
# ==========================================================

github_commit_fields = rostra_conf.model(
    'request', {
        'reponame': fields.String(required=True, description='reponame name. e.g. "rebase-network/rostra-app"'),
        'page': fields.Integer(required=False,min=1, description='page number. e.g. 1'),
        'per_page': fields.Integer(required=False, min=10,description='per_page number. e.g. 10'),
    })


@rostra_conf.route('/github/getcommits/', methods=['POST'])
@rostra_conf.doc(body=github_commit_fields, responses={201: 'Success'})
class GithubGetCommits(Resource):

    @api.response(201, 'Address Deleted')
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            #json = post_github_graphql_commits('rebase-network/rostra-backend')
            #return jsonify(json)
            data = api.payload
            page = 1 if('page' not in data) else int(data['page'])
            per_page = 10 if('per_page' not in data) else  int(data['per_page'])
            
            if(page >=1):
                commits = get_github_repo_commits(data['reponame'],page,per_page)
            else:
                commits=[]
            return jsonify({"result": commits})
        except Exception as e:
            logging.error(e)
            return {'error': str(e)}, 500
github_stars_fields = rostra_conf.model(
    'request', {
        'reponame': fields.String(required=True, description='reponame name. e.g. "rebase-network/rostra-app"'),
        'page': fields.Integer(required=False,min=1, description='page number. e.g. 1,page=0 means not who_starred'),
        'per_page': fields.Integer(required=False, min=10,description='per_page number. e.g. 10'),
    })

@rostra_conf.route('/github/getstars/', methods=['POST'])
@rostra_conf.doc(body=github_stars_fields, responses={201: 'Success'})
class GithubGetStars(Resource):

    @api.response(201, 'Address Deleted')
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            
            page = 1 if('page' not in data) else int(data['page'])
            per_page = 10 if('per_page' not in data) else  int(data['per_page'])
            
            commits = get_github_repo_stars(data['reponame'],page,per_page)
            return jsonify({"result": commits})
        except Exception as e:
            logging.error(e)
            return {'error': str(e)}, 500

# ==========================================================
# 统一接口返回信息
def ResponseInfo(error, message):
    return {'message': message}, error


def ResponseResult(error, result):
    if (error == 200 or error == 201):
        return {'result': result}, error
    else:
        return ResponseInfo(error, 'Error!')

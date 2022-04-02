import json
import uuid

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_restx import Api, Resource, fields

from models import Guild, Nft, Rule, RunResult
from rsa_verify import flashsigner_verify
from runner import run_refresh_rule, runner_start

app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {
    'db': 'guild', 'host': 'localhost', 'port': 27017}

db = MongoEngine()
db.init_app(app)
api = Api(app, version='1.0', title='Rostra Backend API',
          description='Rostra Backend Restful API')
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
        guildInfo = {"name": data["name"], "desc": data["desc"],
                     "creator": data["creator"], "ipfsAddr": data["ipfsAddr"]},

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
        "cota_id": fields.String(required=True, description='The cota id of the nft')
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
                return {'errror': 'The Rule Name Already Exists! Please change your rule name'}, 401

            nft = Nft(name=data['name'],
                      desc=data['desc'],
                      image=data['image'],
                      cota_id=data['cota_id'])
            nft.save()
            return {'message': 'SUCCESS'}, 201
        except Exception as e:
            return {'error': str(e)}, 500


@rostra_conf.route('/nft/get/', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class Get(Resource):
    def get(self):
        nfts = Nft.objects()
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
                return {'errror': 'The Rule Name Already Exists! Please change your rule name'}, 401
            # validation signature
            if len(signature) == 0:
                return {'errror': 'The signature is empty'}, 401

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
                        runnered=False)

            rule.save()
            return {'rule_id': str(rule['id'])}, 201
        except Exception as e:
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


@rostra_conf.route('/runresult/add', methods=['POST'])
class RunresultAdd(Resource):

    @rostra_conf.doc(body=runresult_fields, responses={201: 'RunResult Created'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            print(data)

            if len(RunResult.objects(rule_id=data['rule_id'])) != 0:
                return {'errror': 'The RunResult Already Exists! '}, 401

            runresult = RunResult(
                rule_id=data['rule_id'], result=data['result'])
            runresult.save()
            return {'id': str(runresult['id']), 'rule_id': runresult['rule_id']}, 201
        except Exception as e:
            return {'error': str(e)}, 500

@rostra_conf.route('/runresult/refresh/<rule_id>', methods=['GET'])
class RunresultRefreshByRuleIDGET(Resource):
    @rostra_conf.doc(params={'rule_id': 'rule_id'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def get(self, rule_id):
        try:
            rule = Rule.objects(id=rule_id)
            success = run_refresh_rule(rule[0])
            if success:
                return {'message': 'RuleRunresultRefresh success'}, 201
            else:
                return {'message': 'fail'}, 401
        except Exception as e:
            return {'error': str(e)}, 500


@rostra_conf.route('/runresult/refresh/', methods=['POST'])
class RunresultRefreshByRuleID(Resource):
    @rostra_conf.doc(params={'rule_id': 'rule_id'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            print("/runresult/refresh/", data['rule_id'])
            rule = Rule.objects(id=data['rule_id'])
            success = run_refresh_rule(rule[0])
            if success:
                return {'message': 'RuleRunresultRefresh success'}, 201
            else:
                return {'message': 'fail'}, 401
        except Exception as e:
            return {'error': str(e)}, 500


@rostra_conf.route('/runresult/<id>', methods=['GET'])
@rostra_conf.doc(params={'id': 'id'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultGetByID(Resource):

    def get(self, id):
        try:
            query_by_runresult_id = RunResult.objects(id=id)
            if query_by_runresult_id is not None and len(query_by_runresult_id) != 0:
                return jsonify({"result": query_by_runresult_id[0]})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/runresult/get/walletaddr/<wallet_addr>', methods=['GET'])
@rostra_conf.doc(params={'wallet_addr': 'wallet_addr'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultGetByWallet(Resource):

    def get(self, wallet_addr):
        try:
            query = RunResult.objects(rule_creator=wallet_addr)
            if query is not None and len(query) != 0:
                return jsonify({"result": query})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/runresult/ruleid/<rule_id>', methods=['GET'])
@rostra_conf.doc(params={'rule_id': 'rule_id'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultRuleidGet(Resource):

    def get(self, rule_id):
        try:
            query_by_rule_id = RunResult.objects(rule_id=rule_id)
            if query_by_rule_id is not None and len(query_by_rule_id) != 0:
                return jsonify({"result": query_by_rule_id[0]})
            else:
                return {"result": ''}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}, 500


@rostra_conf.route('/runresult/get', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class RunresultGetAll(Resource):

    def get(self):
        try:
            query = RunResult.objects()
            if query is not None and len(query) != 0:
                return jsonify({"result": query})
            else:
                return {"result": []}, 200
        except Exception as e:
            return {'error': str(e), 'errid': 'err-except'}


@rostra_conf.route('/runresult/delete', methods=['POST'])
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

            query_by_rule_id = RunResult.objects(rule_id=rule_id)

            if query_by_rule_id is not None and len(query_by_rule_id) != 0:
                result = jsonify(query_by_rule_id[0]['result']).json
                if (address in result):
                    result.remove(address)
                    query_by_rule_id.update(result=result)
                    return {'delete': address}, 201
                else:
                    return {'error': 'Address Not Found!'}, 401
            else:
                return {"error": 'The Result cannot be found'}, 401

        except Exception as e:
            return {'error': str(e)}, 500


# Runner end
# ==========================================================
# 统一接口返回信息
def ResponseInfo(error, message):
    return {'error': error, 'message': message}, error

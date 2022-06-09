from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_restx import Api, Resource, fields

from models import MintNftDefine, Nft
from tools import logInit

logInit('rostra_backend.log')

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {'db': 'guild', 'host': 'localhost', 'port': 27017}

db = MongoEngine()
db.init_app(app)
api = Api(app, version='1.0', title='Rostra Backend API', description='Rostra Backend Restful API')
rostra_conf = api.namespace('', description='Rostra APIs')

load_dotenv()

CORS(app)

app.url_map.strict_slashes = False


# nft
nft_model = rostra_conf.model(
    'nft', {
        'name': fields.String(required=True, description='The nft name'),
        "desc": fields.String,
        "image": fields.String(required=True, description='The image url of nft'),
        "cota_id": fields.String(required=True, description='The cota id of the nft'),
        "type": fields.Integer(required=True, description='The type of the nft, 1 - nft, 2- ticket')
    })


#mint nft
mint_nft_model = rostra_conf.model(
    'mint_nft', {
        'account': fields.String(required=True, description='The account address'),
        'name': fields.String(required=True, description='The nft name'),
        "desc": fields.String,
        "image": fields.String(required=True, description='The image url of nft'),
        'total': fields.Integer(required=True, description='The total number of nft'),
        "cotaId": fields.String(required=True, description='The cota id of the nft'),
        'txHash': fields.String(required=True, description='The txHash of the nft'),
        })

@rostra_conf.route('/nft/get/', methods=['GET'])
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class NFTGet(Resource):

    def get(self):
        nfts = Nft.objects(type=1)
        return jsonify({"result": nfts})

@rostra_conf.route('/mint-nft/add/', methods=['POST'])
class MintNFTAdd(Resource):

    @rostra_conf.doc(body=mint_nft_model, responses={201: 'NFT Created'})
    @api.response(500, 'Internal Error')
    @api.response(401, 'Validation Error')
    def post(self):
        try:
            data = api.payload
            print(data)
            # validation if the nft name already exists
            # if len(MintNftDefine.objects(name=data['name'])) != 0:
            #     return ResponseInfo(401, 'The NFT Name Already Exists! Please change your nft name')

            nft = MintNftDefine(
                account=data['account'],
                name=data['name'],
                description=data['desc'],
                image=data['image'],
                total=data['total'],
                cotaId=data['cotaId'],
                txHash=data['txHash'])

            nft.save()
            return {'message': 'SUCCESS'}, 201
        except Exception as e:
            return {'error': str(e)}, 500

@rostra_conf.route('/mint-nft/account/<account>', methods=['GET'])
@rostra_conf.doc(params={'account': 'account address of the User'})
@api.response(200, 'Query Successful')
@api.response(500, 'Internal Error')
class MintNFTDGetByAccount(Resource):

    def get(self, account):
        try:
            query = MintNftDefine.objects(account=account)
            print(query)
            if query is not None and len(query) != 0:
                return jsonify({"result": query})
            else:
                return {"result": []}, 200
        except Exception as e:
            return {'error': str(e)}

# ==========================================================
# 统一接口返回信息
def ResponseInfo(error, message):
    return {'message': message}, error


def ResponseResult(error, result):
    if (error == 200 or error == 201):
        return {'result': result}, error
    else:
        return ResponseInfo(error, 'Error!')

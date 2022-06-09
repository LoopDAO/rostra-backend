import mongoengine as me
from mongoengine import (IntField, StringField)

class Nft(me.Document):
    name = StringField()
    desc = StringField()
    image = StringField()
    cota_id = StringField()
    # 1 - nft
    # 2 - ticket
    type = IntField()

class MintNftDefine(me.Document):
    account=StringField()
    name = StringField()
    description = StringField()
    image = StringField()
    total=IntField()
    cotaId = StringField()
    signature=StringField()
    txHash=StringField()

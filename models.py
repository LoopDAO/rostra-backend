from cgi import test

import mongoengine as me
from mongoengine import (BooleanField, IntField, ListField, ReferenceField,
                         StringField)


class Guild(me.Document):
    guild_id = StringField()
    name = StringField()
    desc = StringField()
    creator = StringField()
    signature = StringField()
    ipfsAddr = StringField()

    def __repr__(self):
        return "%s , %s , %s , %s\n " % (self.guild_id, self.name, self.desc, self.creator)


class Nft(me.Document):
    name = StringField()
    desc = StringField()
    image = StringField()
    cota_id = StringField()
    # 1 - nft
    # 2 - ticket
    type = IntField()


#---------------------------------------------------------------------------------
#rule
class RuleCondition(me.Document):
    x = StringField()
    of = StringField()


class RuleAction(me.EmbeddedDocument):
    type = StringField()
    url = StringField()
    condition = ReferenceField(RuleCondition)
    start_time = StringField()
    end_time = StringField()

    def __repr__(self):
        return "%s , %s , %s , %s\n " % (self.type, self.url, self.action, self.start_time)


class Rule(me.Document):
    rule_id = StringField()
    name = StringField()
    desc = StringField()
    creator = StringField()
    signature = StringField()
    ipfsAddr = StringField()
    action = me.EmbeddedDocumentField(RuleAction)
    nft = StringField()
    finished = BooleanField()

    def __repr__(self):
        return "%s , %s , %s , %s\n " % (self.id, self.name, self.desc, self.creator)


#---------------------------------------------------------------------------------
#Runner
class RunnerCondition(me.Document):
    address = StringField()


class RuleResult(me.Document):  # Runner运行后的结果
    rule_id = StringField()
    rule_name = StringField()
    rule_creator = StringField()
    # address_list_id ->> _id of address list (AddressList)
    address_list_id = StringField()


class AddressList(me.Document):  # Runner运行后获得的address list
    list = ListField(StringField())

from cgi import test
import mongoengine as me
from mongoengine import (StringField, ListField, ReferenceField)


class Guild(me.Document):
    guild_id = StringField()
    name = StringField()
    desc = StringField()
    creator = StringField()
    signature = StringField()
    ipfsAddr = StringField()

    def __repr__(self):
        return "%s , %s , %s , %s\n " % (self.guild_id, self.name, self.desc, self.creator)


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


class RuleNFT(me.EmbeddedDocument):
    name = StringField()
    desc = StringField()
    image = StringField()

    def __repr__(self):
        return "%s , %s , %s\n " % (self.name, self.desc, self.image)


class Rule(me.Document):
    rule_id = StringField()
    name = StringField()
    desc = StringField()
    creator = StringField()
    signature = StringField()
    ipfsAddr = StringField()
    action = me.EmbeddedDocumentField(RuleAction)
    nft = me.EmbeddedDocumentField(RuleNFT)

    def __repr__(self):
        return "%s , %s , %s , %s\n " % (self.id, self.name, self.desc, self.creator)


#---------------------------------------------------------------------------------
#Runner
class RunnerCondition(me.Document):
    address = StringField()


class RunResult(me.Document):
    rule_id = StringField()
    rule_name = StringField()
    rule_creator = StringField()
    #result = ReferenceField(RunnerCondition)
    result = ListField(StringField())

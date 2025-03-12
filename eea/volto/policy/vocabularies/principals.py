""" Vocabulary for users.
"""
from plone import api
from plone.app.vocabularies.principals import UsersFactory as BaseUsersFactory
from plone.app.vocabularies.principals import PrincipalsVocabulary
from zope.schema.vocabulary import SimpleTerm
from zope.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
from plone.restapi.serializer.vocabularies import SerializeTermToJson

from zope.interface import Interface
from plone.restapi.interfaces import ISerializeToJson
from zope.interface import implementer
from zope.component import adapter


class SimpleUserTerm(SimpleTerm):
    def __init__(self, token, value, title):
        super(SimpleUserTerm, self).__init__(token, value, title)


class UsersFactory(BaseUsersFactory):
    """ Factory creating a UsersVocabulary
    """
    @property
    def items(self):
        """Return a list of users"""
        if not self.should_search(query=""):
            return
        acl_users = getToolByName(getSite(), "acl_users")
        userids = set(u.get('id') for u in acl_users.searchUsers())
        for userid in userids:
            user = api.user.get(userid)
            if not user:
                continue
            fullname = user.getProperty("fullname", "")
            if not fullname:
                continue
            email = user.getProperty("email", "")
            yield SimpleUserTerm(email, userid, fullname)

    def __call__(self, *args, **kwargs):
        vocabulary = PrincipalsVocabulary(list(self.items))
        vocabulary.principal_source = self.source
        return vocabulary


@implementer(ISerializeToJson)
@adapter(SimpleUserTerm, Interface)
class SerializeUserTermToJson(SerializeTermToJson):
    def __init__(self, context, request):
        super(SerializeUserTermToJson, self).__init__(context, request)

    def __call__(self):
        termData = super(SerializeUserTermToJson, self).__call__()
        termData["email"] = self.context.value
        print(termData)
        return termData
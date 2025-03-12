""" Vocabulary for users."""

from plone import api
from plone.app.vocabularies.principals import UsersFactory as BaseUsersFactory
from plone.app.vocabularies.principals import PrincipalsVocabulary
from zope.schema.vocabulary import SimpleTerm
from zope.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
from plone.restapi.serializer.vocabularies import SerializeTermToJson
from zope.interface import Interface, implementer
from plone.restapi.interfaces import ISerializeToJson
from zope.component import adapter


class SimpleUserTerm(SimpleTerm):

    def __init__(self, token, value, title):
        super().__init__(token, value, title)


class UsersFactory(BaseUsersFactory):
    """ Factory creating a UsersVocabulary"""

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
    """Serializer for SimpleUserTerm."""

    def __init__(self, context, request):
        super().__init__(context, request)

    def __call__(self):
        termData = super().__call__()
        termData["email"] = self.context.value
        return termData
        
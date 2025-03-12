""" Vocabulary for users."""

# Plone imports
from plone import api
from plone.app.vocabularies.principals import UsersFactory as BaseUsersFactory
from plone.app.vocabularies.principals import PrincipalsVocabulary
from plone.restapi.serializer.vocabularies import SerializeTermToJson
from plone.restapi.interfaces import ISerializeToJson

# Zope imports
from zope.schema.vocabulary import SimpleTerm
from zope.component.hooks import getSite
from zope.interface import Interface, implementer
from zope.component import adapter

# CMFCore imports
from Products.CMFCore.utils import getToolByName


class SimpleUserTerm(SimpleTerm):
    """A simple term representing a user, storing token, value, and title."""

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

    def __call__(self):
        """Serialize user term to JSON."""
        termData = super().__call__()
        termData["email"] = self.context.value
        return termData

""" Vocabulary for users.
"""
from plone import api
from plone.app.vocabularies.principals import UsersFactory as BaseUsersFactory
from plone.app.vocabularies.principals import PrincipalsVocabulary
from zope.schema.vocabulary import SimpleTerm
from zope.component.hooks import getSite
from Products.CMFCore.utils import getToolByName


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
            yield SimpleTerm(userid, userid, fullname)

    def __call__(self, *args, **kwargs):
        vocabulary = PrincipalsVocabulary(list(self.items))
        vocabulary.principal_source = self.source
        return vocabulary

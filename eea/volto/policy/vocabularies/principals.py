"""Vocabulary for users."""

from plone import api
from plone.app.vocabularies.principals import UsersFactory as BaseUsersFactory
from plone.app.vocabularies.principals import (
    PrincipalsVocabulary,
    SOURCES,
    _get_acl_users,
    # merge_principal_infos,
    token_from_principal_info,
)
from zope.schema.vocabulary import SimpleTerm
from zope.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
from zope.globalrequest import getRequest

_USER_SEARCH_UID = {
    "search": "searchUsers",
    # Hint: The fullname search is provided i.e. in IUserEnumeration of
    # the property plugin in PlonePAS.
    "searchattr": "uid",
    "searchargs": {"sort_by": "fullname"},
    "many": "plone.many_users",
}

SOURCES["user"]["searches"] += [_USER_SEARCH_UID]
SOURCES["principal"]["searches"] += [_USER_SEARCH_UID]


def merge_principal_infos(infos, acl_users, prefix=False):
    info = infos[0]
    if len(infos) > 1:
        principal_types = {
            info["principal_type"] for info in infos if info["principal_type"]
        }
        if len(principal_types) > 1:
            # Principals with the same ID but different types. Should not
            # happen.
            raise ValueError("Principal ID not unique: {}".format(info["id"]))
        if not info["title"]:
            for candidate in infos:
                if candidate["title"]:
                    info["title"] = candidate["title"]
                    break

    if (
        info.get("pluginid", "") == "pasldap"
        and info.get("principal_type", "") == "user"
        and info.get("title", None) == info.get("id", "")
    ):
        user = acl_users.getUserById(info["id"])
        info["title"] = user.getProperty("fullname")
    return info


def unique_terms(objects):
    unique_objects = []
    seen_values = set()

    for obj in objects:
        if obj.value not in seen_values:
            unique_objects.append(obj)
            seen_values.add(obj.value)

    return unique_objects


class UsersFactory(BaseUsersFactory):
    """Factory creating a UsersVocabulary"""

    _needs_search = False

    @property
    def items(self):
        """Return a list of users"""
        if not self.should_search(query=""):
            return
        acl_users = getToolByName(getSite(), "acl_users")
        userids = set(u.get("id") for u in acl_users.searchUsers())
        for userid in userids:
            user = api.user.get(userid)
            if not user:
                continue
            fullname = user.getProperty("fullname", "")
            if not fullname:
                continue
            yield SimpleTerm(userid, userid, fullname)

    def should_search(self, query):
        if self._needs_search:
            return True

        return super().should_search(query)

    def __call__(self, *args, **kwargs):
        request = getRequest()
        tokens = request.form.get("tokens", None)
        if tokens:
            self._needs_search = True
            return self.original_tweaked__call__(*args, query=tokens)

        vocabulary = PrincipalsVocabulary(list(self.items))
        vocabulary.principal_source = self.source
        return vocabulary

    def original_tweaked__call__(self, context, query=""):
        if not self.should_search(query):
            vocabulary = PrincipalsVocabulary([])
            vocabulary.principal_source = self.source
            return vocabulary

        acl_users = _get_acl_users()
        cfg = SOURCES[self.source]

        def term_triples():
            """Generator for term triples (value, token, name)"""
            for search_cfg in cfg["searches"]:
                search = getattr(acl_users, search_cfg["search"])
                searchargs = search_cfg["searchargs"].copy()
                searchargs[search_cfg["searchattr"]] = query
                infotree = {}
                for info in search(**searchargs):
                    infotree.setdefault(info["id"], {}).setdefault(
                        info["principal_type"], []
                    ).append(info)

                for principal_id, types_infos in infotree.items():
                    if len(types_infos) > 1 and not cfg["prefix"]:
                        raise ValueError(
                            f"Principal ID not unique: {principal_id}")
                    for principal_type, principal_infos in types_infos.items():
                        if principal_type == "user":
                            pass
                        value = principal_id
                        info = merge_principal_infos(
                            principal_infos, acl_users)
                        if cfg["prefix"]:
                            value = "{}:{}".format(
                                info["principal_type"], value)
                        token = token_from_principal_info(
                            info, prefix=cfg["prefix"])
                        yield (value, token, info["title"])

        terms = unique_terms(
            [
                SimpleTerm(*term_triple)
                for term_triple in filter(self.use_principal_triple, term_triples())
            ]
        )
        vocabulary = PrincipalsVocabulary(terms)
        vocabulary.principal_source = self.source
        return vocabulary

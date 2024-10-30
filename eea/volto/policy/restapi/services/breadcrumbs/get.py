""" Breadcrumbs """
from plone.restapi.services.breadcrumbs.get import Breadcrumbs
from zope.component import getMultiAdapter
from zope.interface import implementer
from plone.restapi.interfaces import IExpandableElement, IPloneRestapiLayer
from zope.interface import Interface
from zope.component import adapter


@implementer(IExpandableElement)
@adapter(Interface, IPloneRestapiLayer)
class EEABreadcrumbs(Breadcrumbs):
    """ EEA Breadcrumbs """

    def __call__(self, expand=False):
        """ """
        result = {"breadcrumbs": {
            "@id": f"{self.context.absolute_url()}/@breadcrumbs"}}
        if not expand:
            return result

        portal_state = getMultiAdapter(
            (self.context, self.request), name="plone_portal_state"
        )
        breadcrumbs_view = getMultiAdapter(
            (self.context, self.request), name="breadcrumbs_view"
        )
        items = []
        # EEA add portal_type info to breadcrumbs
        for crumb in breadcrumbs_view.breadcrumbs():
            item = {
                "title": crumb["Title"],
                "portal_type": crumb['portal_type'],
                "@id": crumb["absolute_url"],
            }
            if crumb.get("nav_title", False):
                item.update({"title": crumb["nav_title"]})

            items.append(item)

        result["breadcrumbs"]["items"] = items
        result["breadcrumbs"]["root"] = portal_state.navigation_root().absolute_url()
        return result

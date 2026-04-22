"""Breadcrumbs"""

from zope.component import getMultiAdapter
from zope.component import adapter
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import Interface
from plone.restapi.interfaces import IExpandableElement, IPloneRestapiLayer
from plone.restapi.services.actions.get import Actions


@implementer(IExpandableElement)
@adapter(Interface, IPloneRestapiLayer)
class EEAActions(Actions):
    """EEA Actions"""

    def __call__(self, expand=False):
        """ """
        result = {"actions": {"@id": f"{self.context.absolute_url()}/@actions"}}
        if not expand:
            return result

        context_state = getMultiAdapter(
            (self.context, self.request), name="plone_context_state"
        )

        categories = self.request.form.get("categories", self.all_categories)
        filtered_action_props = {
            "category",
            "link_target",
            "available",
            "visible",
            "allowed",
            "modal",
        }
        data = {}
        for category in categories:
            category_action_data = []
            actions = context_state.actions(category=category)
            for action in actions:
                # EEA allow actions props to be served by the endpoint except
                # for the ones listed in filtered_action_props
                action_data = {
                    key: translate(value, context=self.request)
                    if key == "title"
                    else value
                    for key, value in action.items()
                    if key not in filtered_action_props
                }

                category_action_data.append(action_data)
            data[category] = category_action_data
        return {"actions": data}

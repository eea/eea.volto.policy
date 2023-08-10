""" Set effective date Action:
    - sets the effective/publishing date of object, if is missing
    - adds an entry in object's workflow history (optional)
"""
from logging import getLogger
from zope.interface import implements, Interface
from zope.component import adapts
from zope.formlib import form
from zope import schema
from OFS.SimpleItem import SimpleItem
from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

logger = getLogger("Products.EEAContentTypes")

class ISetEffectiveDateAction(Interface):
    """Interface for the configurable aspects of the action.
    """

    hist_entry = schema.Choice(
        title=_(u"Add an entry in workflow history"),
        description=_(
            u"An entry will be added in the object's workflow history."
        ),
        values=["Yes", "No"],
        required=True,
        default=_(u"Yes")
        )

    entry_action = schema.TextLine(
        title=_(u'History entry action (required if \'Yes\' is selected)'),
        description=_(u'Workflow action short description'),
        required=False,
        default=_(u"Publish")
        )

    entry_comment = schema.TextLine(
        title=_(u'History entry comment (optional)'),
        description=_(u'Workflow action comment'),
        required=False
        )

class SetEffectiveDateAction(SimpleItem):
    """The actual persistent implementation of the action element.
    """
    implements(ISetEffectiveDateAction, IRuleElementData)

    element = 'Products.EEAContentTypes.actions.set_effective_date'
    summary = _(
        u"Set effective/publishing date if missing; " +
        u"add an entry in object's workflow history (optional)"
    )

    hist_entry = ''
    entry_action = ''
    entry_comment = ''

class SetEffectiveDateActionExecutor(object):
    """The executor for this action.
    """
    implements(IExecutable)
    adapts(Interface, ISetEffectiveDateAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        obj = self.event.object

        hist_entry = self.element.hist_entry
        entry_action = self.element.entry_action
        entry_comment = self.element.entry_comment

        mod_date_field = obj.getField('modification_date')
        eff_date_field = obj.getField('effectiveDate')
        effective_date = eff_date_field.getAccessor(obj)()

        if not effective_date:
            try:
                d = DateTime()
                eff_date_field.getMutator(obj)(d)
                mod_date_field.getMutator(obj)(d)
                obj.reindexObject(
                    idxs=['effective', 'effectiveRange', 'modification_date']
                )
            except Exception, e:
                logger.error(
                    'Got exception \'%s\' while setting effective date' +
                    ' for \'%s\'', e, '/'.join(obj.getPhysicalPath())
                )

        if hist_entry == 'Yes' and entry_action:
            try:
                self.addWfHistEntry(
                    obj,
                    action=entry_action,
                    comment=entry_comment
                )
            except Exception, e:
                logger.error(
                    'Got exception \'%s\' while adding workflow history entry' +
                    ' for \'%s\'', e, '/'.join(obj.getPhysicalPath())
                )

    def addWfHistEntry(self, obj, action='', comment=''):
        """Adds an entry in the workflow history of object
        """
        if not action:
            return

        wf_tool = getToolByName(obj, "portal_workflow")
        wf_chain = wf_tool.getChainFor(obj)
        if len(wf_chain) == 1:
            wf_id = wf_chain[0]
        else:
            raise Exception("Object is assigned to multiple workflows or none!")

        pm_tool = getToolByName(obj, 'portal_membership')
        auth_usr = pm_tool.getAuthenticatedMember().getId()
        review_state = wf_tool.getInfoFor(obj, 'review_state')
        status = {
            'actor': auth_usr,
            'action': action,
            'review_state': review_state,
            'time': DateTime(),
            'comments': comment
            }

        wf_tool.setStatusOf(wf_id, obj, status)

class SetEffectiveDateAddForm(AddForm):
    """An add form for the action
    """
    label = _(u"Add Set effective/publishing date action")
    description = _(
        u"Set effective/publishing date if missing; " +
        u"add an entry in object's workflow history"
    )
    form_name = _(u"Configure action")
    form_fields = form.FormFields(ISetEffectiveDateAction)

    def create(self, data):
        """ Action create method
        """
        a = SetEffectiveDateAction()
        form.applyChanges(a, self.form_fields, data)
        return a

class SetEffectiveDateEditForm(EditForm):
    """An edit form for the action
    """
    label = _(u"Edit Set effective/publishing date action")
    description = _(
        u"Set effective/publishing date if missing; " +
        u"add an entry in object's workflow history"
    )
    form_name = _(u"Configure action")
    form_fields = form.FormFields(ISetEffectiveDateAction)
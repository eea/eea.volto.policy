from AccessControl.ZopeGuards import guarded_getattr
from plone.namedfile.browser import Download
from plone.rfc822.interfaces import IPrimaryFieldInfo
from zope.publisher.interfaces import NotFound


class SafeDownload(Download):
    """Download view that returns 404 instead of 500 when there is no
    primary file field on the context.
    """

    def _getFile(self):
        if not self.fieldname:
            info = IPrimaryFieldInfo(self.context, None)
            if info is None:
                raise NotFound(self, "", self.request)
            self.fieldname = info.fieldname
            if self.fieldname is None:
                raise NotFound(self, "", self.request)

            guarded_getattr(self.context, self.fieldname, None)

            file = info.value
        else:
            context = getattr(self.context, "aq_explicit", self.context)
            file = guarded_getattr(context, self.fieldname, None)

        if file is None:
            raise NotFound(self, self.fieldname, self.request)

        return file

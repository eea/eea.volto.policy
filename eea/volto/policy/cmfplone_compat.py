try:
    from Products.CMFPlone.resources.browser.scripts import ScriptsView
    from Products.CMFPlone.resources.browser.styles import StylesView
except ImportError:
    from Products.CMFPlone.resources.browser.resource import ScriptsView
    from Products.CMFPlone.resources.browser.resource import StylesView

__all__ = ("ScriptsView", "StylesView")

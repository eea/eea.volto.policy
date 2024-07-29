""" RestAPI serializer
"""
from plone.app.layout.navigation.root import getNavigationRoot
from plone.restapi.services.contextnavigation import get as original_get


class EEAContextNavigationQueryBuilder(original_get.QueryBuilder):
    """ Custom QueryBuilder for context navigation
    """
    def __init__(self, context, data):
        super().__init__(context, data)

        depth = data.bottomLevel

        if depth == 0:
            depth = 999

        root = original_get.get_root(context, data.root_path)
        if root is not None:
            rootPath = "/".join(root.getPhysicalPath())
        else:
            rootPath = getNavigationRoot(context)

        # EEA modification to always use the rootPath for query
        self.query["path"] = {"query": rootPath, "depth": depth, "navtree": 1}

        topLevel = data.topLevel
        if topLevel and topLevel > 0:
            # EEA modification to use bottomLevel for depth of navtree_start
            self.query["path"]["navtree_start"] = depth + 1  # 4

# Apply the patch
original_get.QueryBuilder = EEAContextNavigationQueryBuilder

"""Make hideChildrenFromNavigation behavior available"""
import logging

logger = logging.getLogger(__name__)


def add_hidechildren_behavior(setup_tool):
    """Import componentregistry to make new behavior available"""
    logger.info("Importing componentregistry to register new behaviors")
    setup_tool.runImportStepFromProfile('eea.volto.policy:default', 'componentregistry')
    logger.info("Finished importing componentregistry")
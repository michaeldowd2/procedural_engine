from .numeric_handler import NumericHandler
from .categorical_handler import CategoricalHandler
from .rule_item_list_handler import RuleItemListHandler
from .item_list_handler import ItemListHandler
from .entity_list_handler import EntityListHandler
from .wfc_handler import WFCHandler

def get_default_handlers():
    return {
        "numeric": NumericHandler(),
        "categorical": CategoricalHandler(),
        "rule_item_list": RuleItemListHandler(),
        "item_list": ItemListHandler(),
        "entity_list": EntityListHandler(),
        "wfc_grid": WFCHandler()
    }

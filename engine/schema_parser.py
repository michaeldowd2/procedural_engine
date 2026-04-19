import json
from collections import OrderedDict

class SchemaParser:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.schema = json.load(f)
            
        self.properties = self.schema.get("properties", [])
        self.prop_dict = OrderedDict()
        for prop in self.properties:
            self.prop_dict[prop["name"]] = prop
            
    def get_property(self, name):
        return self.prop_dict.get(name)

    def get_all_properties(self):
        return self.properties

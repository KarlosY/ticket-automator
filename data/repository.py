# data/repository.py
import json
import os

class Repository:
    def __init__(self, templates_file, requesters_file):
        self.templates_file = templates_file
        self.requesters_file = requesters_file

    def get_templates(self):
        if os.path.exists(self.templates_file):
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_requesters(self):
        if os.path.exists(self.requesters_file):
            with open(self.requesters_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_templates(self, data):
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    def save_requesters(self, data):
        with open(self.requesters_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

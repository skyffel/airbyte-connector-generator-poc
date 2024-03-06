import os
import json


class LocalCache():
    def __init__(self, cache_file_path):
        if not cache_file_path.endswith('.json'):
            raise ValueError("Cache file path must end with '.json'")
        self.cache_file_path = cache_file_path
        if not os.path.exists(self.cache_file_path):
            with open(self.cache_file_path, 'w') as cache_file:
                # Create an empty JSON object in the file
                cache_file.write('{}')

    def get(self, key):
        with open(self.cache_file_path, 'r') as cache_file:
            file_content = cache_file.read()
            cache_data = json.loads(file_content if file_content else '{}')
        return cache_data.get(key)

    def set(self, key: str, value: dict):
        with open(self.cache_file_path, 'r') as cache_file:
            cache_data = json.loads(cache_file.read())
        cache_data[key] = value
        with open(self.cache_file_path, 'w') as cache_file:
            cache_file.write(json.dumps(cache_data, indent=2))

    def __del__(self):
        pass

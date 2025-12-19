import json
import os

CONFIG_FILE = 'grsai_config.json'

DEFAULT_CONFIG = {
    "api_base_url": "https://grsai.dakka.com.cn",
    "api_key": "",
    "output_folder": os.path.join(os.getcwd(), "output"),
    "nano_banana_last_model": "nano-banana-fast",
    "nano_banana_last_aspect_ratio": "auto",
    "nano_banana_last_image_size": "1K",
    "gpt_image_last_model": "sora-image",
    "gpt_image_last_size": "1:1",
    "gpt_image_last_variants": 1
}

class Config:
    def __init__(self):
        self.data = self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG

    def save_config(self, data=None):
        if data is None:
            data = self.data
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save_config()

cfg = Config()

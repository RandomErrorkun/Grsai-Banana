import json
import os

from core.model_catalog import LEGACY_IMAGE_MODEL_ALIASES

CONFIG_FILE = 'grsai_config.json'

DEFAULT_CONFIG = {
    "api_base_url": "https://grsai.dakka.com.cn",
    "api_key": "",
    "output_folder": "./output",
    "last_model": "nano-banana-2-lite",
    # Nano Banana parameters
    "nano_banana_aspect_ratio": "auto",
    "nano_banana_image_size": "1K",
    # GPT Image parameters
    "gpt_image_size": "auto",
    "gpt_image_quality": "auto",
    "gpt_image_tier": "1K",
    "gpt_transparent_background": False,
    # Video generation parameters
    "video_aspect_ratio": "landscape",
    "video_resolution": "480p",
    "video_duration": 5,
    "video_parallel_tasks": 1,
    # Shared parameters
    "auto_retry_on_failure": False,
    "vip_moderation_auto_retry": False,
    "parallel_tasks": 1,
    "comic_parallel_tasks": 2,
    "max_retries": 5,
    "theme": "auto",
    "language": "en",
    "text_format_enabled": True,
    "text_font_size": 12,
    "text_font_family": "Arial",
    "text_auto_wrap": True,
    "comic_story_model": "gemini-3.1-pro",
    "comic_image_model": "nano-banana-2-lite",
    "comic_page_count": 6,
    "comic_aspect_ratio": "3:4",
    "comic_image_size": "1K",
    "comic_last_project": "",
    # History page settings
    "history_items_per_page": 5,
    "last_tab": "banana_pro"
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
                loaded = json.load(f)
                # Migrate old config format to new one
                loaded = self._migrate_config(loaded)
                return loaded
        except:
            return DEFAULT_CONFIG
    
    def _migrate_config(self, old_config):
        """Migrate old config format to new one"""
        migrated = old_config.copy()
        
        # Migrate old last_aspect_ratio and last_image_size to nano_banana_*
        if "last_aspect_ratio" in migrated:
            migrated["nano_banana_aspect_ratio"] = migrated.pop("last_aspect_ratio", "auto")
        if "last_image_size" in migrated:
            migrated["nano_banana_image_size"] = migrated.pop("last_image_size", "1K")

        # Migrate old Google Gemini setup to Grsai Nano Banana
        if migrated.get("api_base_url", "").startswith("https://generativelanguage.googleapis.com"):
            migrated["api_base_url"] = DEFAULT_CONFIG["api_base_url"]

        legacy_model_map = {
            **LEGACY_IMAGE_MODEL_ALIASES,
        }
        last_model = migrated.get("last_model")
        if last_model in legacy_model_map:
            migrated["last_model"] = legacy_model_map[last_model]

        comic_image_model = migrated.get("comic_image_model")
        if comic_image_model in legacy_model_map:
            migrated["comic_image_model"] = legacy_model_map[comic_image_model]

        for key, value in list(migrated.items()):
            if key.startswith("last_model_") and value in legacy_model_map:
                migrated[key] = legacy_model_map[value]

        # Migrate old tab names to stable tab keys used by i18n
        tab_key_map = {
            "Banana 1": "banana_pro",
            "Banana Pro": "banana_pro",
            "GPT Image": "gpt_image",
        }
        old_last_tab = migrated.get("last_tab")
        if old_last_tab in tab_key_map:
            migrated["last_tab"] = tab_key_map[old_last_tab]

        # The standalone Banana 1 tab has been removed; fold it into Banana Pro.
        if migrated.get("last_tab") == "banana_1":
            migrated["last_tab"] = "banana_pro"

        # Carry over the last selected model of the removed Banana 1 tab into Banana Pro
        # only when the Banana Pro tab has no remembered model yet.
        legacy_banana_1_model_key = "last_model_tab_banana_1"
        banana_pro_model_key = "last_model_tab_banana_pro"
        if legacy_banana_1_model_key in migrated and banana_pro_model_key not in migrated:
            legacy_value = migrated[legacy_banana_1_model_key]
            if legacy_value in legacy_model_map:
                legacy_value = legacy_model_map[legacy_value]
            migrated[banana_pro_model_key] = legacy_value

        for old_name, new_key in tab_key_map.items():
            old_model_key = f"last_model_{old_name}"
            new_model_key = f"last_model_tab_{new_key}"
            if old_model_key in migrated and new_model_key not in migrated:
                migrated[new_model_key] = migrated[old_model_key]
        
        # Ensure all required keys exist
        for key, value in DEFAULT_CONFIG.items():
            if key not in migrated:
                migrated[key] = value
        
        return migrated

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

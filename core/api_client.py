import requests
import json
from core.config import cfg

class NanoBananaApiClient:
    def __init__(self):
        pass

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.get('api_key')}"
        }

    def submit_task(self, prompt, model, aspect_ratio="auto", image_size="1K", ref_image_urls=None):
        url = f"{cfg.get('api_base_url').rstrip('/')}/v1/draw/nano-banana"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "imageSize": image_size,
            "webHook": "-1",  # Use -1 to get ID immediately for polling
            "shutProgress": False
        }

        if ref_image_urls:
            payload["urls"] = ref_image_urls

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"code": -1, "msg": str(e)}

    def get_task_result(self, task_id):
        url = f"{cfg.get('api_base_url').rstrip('/')}/v1/draw/result"
        payload = {"id": task_id}

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"code": -1, "msg": str(e)}

class GptImageClient:
    def __init__(self):
        pass

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.get('api_key')}"
        }

    def submit_task(self, prompt, model="sora-image", size="1:1", variants=1, ref_image_urls=None):
        url = f"{cfg.get('api_base_url').rstrip('/')}/v1/draw/completions"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "variants": variants,
            "webHook": "-1",  # Use -1 to get ID immediately for polling
            "shutProgress": False
        }

        if ref_image_urls:
            payload["urls"] = ref_image_urls

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"code": -1, "msg": str(e)}

    def get_task_result(self, task_id):
        url = f"{cfg.get('api_base_url').rstrip('/')}/v1/draw/result"
        payload = {"id": task_id}

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"code": -1, "msg": str(e)}

nano_banana_api = NanoBananaApiClient()
gpt_image_api = GptImageClient()

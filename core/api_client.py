import requests
import os
import base64
import random
from core.config import cfg
from core.model_catalog import (
    NANO_MODELS,
    NANO_IMAGE_SIZE_OPTIONS,
    COMPLETION_MODELS,
    VIDEO_MODEL_SET,
    GPT_IMAGE_QUALITY_OPTIONS,
    GPT_TRANSPARENT_MODELS,
    LEGACY_IMAGE_MODEL_ALIASES,
    video_duration_limit,
    VIDEO_MAX_DURATION,
)

class ApiClient:
    """Grsai 统一生成接口客户端（/v1/api/generate + /v1/api/result）。"""

    LEGACY_MODEL_ALIASES = {
        **LEGACY_IMAGE_MODEL_ALIASES,
    }
    LEGACY_COMPLETION_MODELS = {"sora-2", "veo3.1-fast-1080p"}

    GENERATE_PATH = "/v1/api/generate"
    RESULT_PATH = "/v1/api/result"

    def __init__(self):
        pass

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.get('api_key')}"
        }

    def _get_base_url(self):
        base_url = cfg.get("api_base_url", "").strip()
        return base_url or "https://grsai.dakka.com.cn"

    def _normalize_model(self, model):
        return self.LEGACY_MODEL_ALIASES.get(model, model)

    def _convert_image_to_data_uri(self, image_path):
        """Convert local image file to data URI for API submission"""
        return self._convert_file_to_data_uri(image_path, "image")

    def _convert_audio_to_data_uri(self, audio_path):
        """Convert local audio file to data URI for API submission"""
        return self._convert_file_to_data_uri(audio_path, "audio")

    def _convert_file_to_data_uri(self, file_path, media_kind):
        try:
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    b64_string = base64.b64encode(f.read()).decode('utf-8')
                ext = os.path.splitext(file_path)[1].lower().replace('.', '')
                mime = self._mime_for_extension(ext, media_kind)
                return f"data:{media_kind}/{mime};base64,{b64_string}"
        except Exception as e:
            print(f"Error converting {media_kind} to data URI: {e}")
        return None

    @staticmethod
    def _mime_for_extension(ext, media_kind):
        if media_kind == "audio":
            return {
                "mp3": "mpeg",
                "wav": "wav",
                "m4a": "mp4",
                "aac": "aac",
                "flac": "flac",
                "ogg": "ogg",
            }.get(ext, "mpeg")
        if ext == 'jpg':
            return 'jpeg'
        return ext

    def _convert_paths_to_data_uris(self, paths, media_kind="image"):
        if not paths:
            return None
        converted = []
        for path in paths:
            if os.path.isfile(path):  # It's a local file path
                data_uri = (
                    self._convert_image_to_data_uri(path)
                    if media_kind == "image"
                    else self._convert_audio_to_data_uri(path)
                )
                if data_uri:
                    converted.append(data_uri)
            else:  # It's already a URL or data URI
                converted.append(path)
        return converted or None

    def _normalize_chat_messages(self, messages):
        normalized = []
        for message in messages or []:
            if not isinstance(message, dict):
                normalized.append(message)
                continue

            normalized_message = dict(message)
            content = normalized_message.get("content")
            if isinstance(content, list):
                normalized_content = []
                for item in content:
                    if not isinstance(item, dict):
                        normalized_content.append(item)
                        continue

                    normalized_item = dict(item)
                    if item.get("type") == "image_url":
                        image_url = item.get("image_url")
                        if isinstance(image_url, dict):
                            url = image_url.get("url")
                            if isinstance(url, str) and os.path.isfile(url):
                                data_uri = self._convert_image_to_data_uri(url)
                                if data_uri:
                                    normalized_item["image_url"] = dict(image_url)
                                    normalized_item["image_url"]["url"] = data_uri
                        elif isinstance(image_url, str) and os.path.isfile(image_url):
                            data_uri = self._convert_image_to_data_uri(image_url)
                            if data_uri:
                                normalized_item["image_url"] = {"url": data_uri}
                    normalized_content.append(normalized_item)
                normalized_message["content"] = normalized_content
            normalized.append(normalized_message)
        return normalized

    def chat_completion(self, model, messages, stream=False, temperature=None):
        """Call OpenAI-compatible chat completions API."""
        url = f"{self._get_base_url().rstrip('/')}/v1/chat/completions"
        payload = {
            "model": model,
            "stream": stream,
            "messages": self._normalize_chat_messages(messages),
        }

        if temperature is not None:
            payload["temperature"] = temperature

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": {"message": str(e)}}
        except Exception as e:
            return {"error": {"message": str(e)}}

    def build_generate_payload(self, prompt, model, aspect_ratio="auto", image_size="1K",
                               ref_image_urls=None, quality=None, background=None,
                               duration=None, seed=None, ref_audios=None):
        """根据模型构造 /v1/api/generate 请求体（不含 replyType）。"""
        model = self._normalize_model(model)

        if model in NANO_MODELS:
            payload = {
                "model": model,
                "prompt": prompt,
                "aspectRatio": aspect_ratio or "auto",
            }
            if model in NANO_IMAGE_SIZE_OPTIONS and image_size:
                allowed_sizes = NANO_IMAGE_SIZE_OPTIONS[model]
                payload["imageSize"] = image_size if image_size in allowed_sizes else allowed_sizes[0]
            if ref_image_urls:
                payload["images"] = ref_image_urls
            return payload

        if model in COMPLETION_MODELS or model in self.LEGACY_COMPLETION_MODELS:
            payload = {
                "model": model,
                "prompt": prompt,
                "aspectRatio": aspect_ratio or "auto",
            }
            quality_options = GPT_IMAGE_QUALITY_OPTIONS.get(model) or ["auto"]
            payload["quality"] = quality if quality in quality_options else quality_options[0]
            if background == "transparent" and model in GPT_TRANSPARENT_MODELS:
                payload["background"] = "transparent"
            if ref_image_urls:
                payload["images"] = ref_image_urls
            return payload

        if model in VIDEO_MODEL_SET:
            resolution = image_size if image_size in ("480p", "768p", "1080p") else "480p"
            try:
                duration_value = int(duration)
            except (TypeError, ValueError):
                duration_value = 5
            duration_value = max(1, min(duration_value, video_duration_limit(resolution), VIDEO_MAX_DURATION))
            try:
                seed_value = int(seed)
            except (TypeError, ValueError):
                seed_value = random.randint(1, 2 ** 31 - 1)
            payload = {
                "model": model,
                "prompt": prompt,
                "aspectRatio": aspect_ratio if aspect_ratio in ("portrait", "landscape", "square") else "landscape",
                "images": ref_image_urls or [],
                "audios": ref_audios or [],
                "seed": seed_value,
                "resolution": resolution,
                "duration": duration_value,
            }
            return payload

        return None

    def submit_task(self, prompt, model, aspect_ratio="auto", image_size="1K", ref_image_urls=None,
                    variants=1, quality=None, background=None, duration=None, seed=None, ref_audios=None):
        """Submit task to the unified generate API (/v1/api/generate, replyType=async)."""
        model = self._normalize_model(model)

        # Convert local file paths to data URIs for API submission
        ref_image_urls = self._convert_paths_to_data_uris(ref_image_urls, "image")
        ref_audios = self._convert_paths_to_data_uris(ref_audios, "audio")

        payload = self.build_generate_payload(
            prompt, model,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            ref_image_urls=ref_image_urls,
            quality=quality,
            background=background,
            duration=duration,
            seed=seed,
            ref_audios=ref_audios,
        )
        if payload is None:
            return {"code": -1, "msg": f"Unknown model: {model}"}

        payload["replyType"] = "async"
        return self._post_generate(payload)

    def _post_generate(self, payload):
        url = f"{self._get_base_url().rstrip('/')}{self.GENERATE_PATH}"
        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=60)
            try:
                data = response.json()
            except ValueError:
                return {"code": -1, "msg": f"HTTP {response.status_code}: invalid JSON response"}

            if response.status_code == 200 and isinstance(data, dict) and data.get("id"):
                return {"code": 0, "data": data}

            if isinstance(data, dict):
                msg = data.get("error") or data.get("msg") or f"HTTP {response.status_code}"
                return {"code": -1, "msg": msg, "status": data.get("status")}
            return {"code": -1, "msg": f"HTTP {response.status_code}: {data}"}
        except requests.exceptions.RequestException as e:
            return {"code": -1, "msg": str(e)}
        except Exception as e:
            return {"code": -1, "msg": str(e)}

    def get_task_result(self, task_id):
        """Query the unified result API (GET /v1/api/result?id=...).

        Raises on transport errors so callers can apply their own retry policy.
        """
        url = f"{self._get_base_url().rstrip('/')}{self.RESULT_PATH}"
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {cfg.get('api_key')}"},
                params={"id": task_id},
                timeout=30,
            )
            try:
                data = response.json()
            except ValueError:
                raise RuntimeError(f"HTTP {response.status_code}: invalid JSON response")

            if isinstance(data, dict) and data.get("id"):
                return {"code": 0, "data": data}

            if response.status_code == 200:
                # 200 但缺少任务 id，视为服务端异常数据
                raise RuntimeError(str(data)[:200])
            raise RuntimeError(f"HTTP {response.status_code}: {str(data)[:200]}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(str(e))

api = ApiClient()

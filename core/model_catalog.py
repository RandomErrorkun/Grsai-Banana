TAB_BANANA_PRO = "banana_pro"
TAB_GPT_IMAGE = "gpt_image"
TAB_VIDEO = "video"

CHAT_MODELS = [
    "gemini-3.1-pro",
    "gemini-3-pro",
    "gemini-2.5-pro",
]

# --- 模型底座对照（核实日期：2026-09-15，来源：Grsai 官网 + api_docs/）---
# 注意：Grsai 是中转站，模型命名、底座映射与参数支持随时可能调整；
# 以下信息仅代表标注日期当时的状态，升级维护时请以官网/接口文档的实时信息复核：
#   nano-banana / nano-banana-fast  由 gemini-3.1-flash-lite-image 封装
#       （nano-banana-fast 为特价版，仅支持 1K 分辨率）
#   nano-banana-2-lite              2026-09-15 时与 nano-banana-fast 同底座（gemini-3.1-flash-lite-image），
#                                   仅支持 1K；因 nano-banana-fast 是中转站自定义命名、日后可能被
#                                   换接其他模型，故 2026-09-16 起保留为一等模型独立入口
#   nano-banana-2                   底座为 gemini-3-flash-image
#   nano-banana-2.1                 2026-10-09 官方更新报告新增；配置与请求同 nano-banana-2
#   nano-banana-pro                 底座为 gemini-2.5-pro-image
#   gemini-2.5-flash-image          2026-09-15 核实时已下架（不在接口文档模型列表中），
#                                   代码中仅作为旧历史记录的迁移别名保留，不会提交给服务端
BANANA_PRO_MODELS = [
    "nano-banana",
    "nano-banana-fast",
    "nano-banana-2",
    "nano-banana-2.1",
    "nano-banana-2-lite",
    "nano-banana-2-cl",
    "nano-banana-2-2k-cl",
    "nano-banana-2-4k-cl",
    "nano-banana-pro",
    "nano-banana-pro-vt",
    "nano-banana-pro-cl",
    "nano-banana-pro-vip",
    "nano-banana-pro-4k-vip",
]

GPT_IMAGE_MODELS = [
    "gpt-image-2",
    "gpt-image-2-vip",
    "gpt-image-2.5",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
]

VIDEO_MODELS = [
    "minimax-h3",
]

LEGACY_IMAGE_MODEL_ALIASES = {
    "gpt-image-1.5": "gpt-image-2",
    "sora-image": "gpt-image-2",
    # nano-banana-2-lite 已恢复为一等模型（2026-09-16），不再做别名替换
    # 2026-09-15 核实 gemini-2.5-flash-image 已从中转站下架，别名仅供旧历史记录恢复参数使用
    "gemini-2.5-flash-image": "nano-banana-fast",
}

COMIC_IMAGE_MODELS = BANANA_PRO_MODELS + GPT_IMAGE_MODELS

TAB_MODELS = {
    TAB_BANANA_PRO: BANANA_PRO_MODELS,
    TAB_GPT_IMAGE: GPT_IMAGE_MODELS,
}

NANO_IMAGE_SIZE_OPTIONS = {
    # 2026-09-15 官网确认：nano-banana / nano-banana-fast / nano-banana-2-lite
    # 同底座（gemini-3.1-flash-lite-image），均仅支持 1K
    "nano-banana": ["1K"],
    "nano-banana-fast": ["1K"],
    "nano-banana-2": ["1K", "2K", "4K"],
    "nano-banana-2.1": ["1K", "2K", "4K"],
    "nano-banana-2-lite": ["1K"],
    "nano-banana-2-cl": ["1K"],
    "nano-banana-2-2k-cl": ["2K"],
    "nano-banana-2-4k-cl": ["4K"],
    "nano-banana-pro": ["1K", "2K", "4K"],
    "nano-banana-pro-vt": ["1K", "2K", "4K"],
    "nano-banana-pro-cl": ["1K", "2K", "4K"],
    "nano-banana-pro-vip": ["1K", "2K"],
    "nano-banana-pro-4k-vip": ["4K"],
}

NANO_BASE_RATIOS = [
    "auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9",
]
# nano-banana-2 系列额外支持的比例（依据 api_docs/nano-banana接口.md，2026-09-15 版本）
NANO_EXTENDED_RATIOS = NANO_BASE_RATIOS + ["1:4", "4:1", "1:8", "8:1"]


def nano_ratio_options(model_name):
    if (model_name or "").startswith("nano-banana-2"):
        return list(NANO_EXTENDED_RATIOS)
    return list(NANO_BASE_RATIOS)


# gpt-image-2 / gpt-image-2.5：支持比例或 1K 像素值（依据 api_docs/gpt-image-2_gpt-image-2.5接口.md，2026-09-15 版本）
GPT_IMAGE_RATIOS = [
    "auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3",
    "5:4", "4:5", "21:9", "9:21", "1:2", "2:1",
]

# vip 系模型只支持像素值，比例需按 1K/2K/4K 档位换算成像素（同上文档，2026-09-15 版本）
GPT_PIXEL_ONLY_MODELS = [
    "gpt-image-2-vip",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
]
GPT_TRANSPARENT_MODELS = [
    "gpt-image-2-vip",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
]
GPT_VIP_RATIOS = [
    "auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3",
    "5:4", "4:5", "21:9", "9:21", "1:3", "3:1", "2:1", "1:2",
]
GPT_PIXEL_TIERS = ["1K", "2K", "4K"]

# 官方文档给出的 vip 系模型比例 -> 像素参考表（依次为 1K/2K/4K，部分比例无 4K；2026-09-15 版本）
GPT_PIXEL_MAP = {
    "1:1": ["1024x1024", "2048x2048", "2880x2880"],
    "16:9": ["1280x720", "2048x1152", "3840x2160"],
    "9:16": ["720x1280", "1152x2048", "2160x3840"],
    "4:3": ["1152x864", "2304x1728", "3264x2448"],
    "3:4": ["864x1152", "1728x2304", "2448x3264"],
    "3:2": ["1536x1024", "2048x1360", "3504x2336"],
    "2:3": ["1024x1536", "1360x2048", "2336x3504"],
    "5:4": ["1120x896", "2240x1792", "3200x2560"],
    "4:5": ["896x1120", "1792x2240", "2560x3200"],
    "21:9": ["1456x624", "2912x1248", "3840x1648"],
    "9:21": ["624x1456", "1248x2912", "1648x3840"],
    "1:3": ["688x2048", "1280x3840"],
    "3:1": ["2048x688", "3840x1280"],
    "2:1": ["1536x768", "3072x1536", "3840x1920"],
    "1:2": ["768x1536", "1536x3072", "1920x3840"],
}

# 各模型支持的质量档位（依据 api_docs/gpt-image-2_gpt-image-2.5接口.md，2026-09-15 版本）
GPT_IMAGE_QUALITY_OPTIONS = {
    "gpt-image-2": ["auto"],
    "gpt-image-2.5": ["auto"],
    "gpt-image-2-vip": ["medium"],
    "gpt-image-2.5-flare": ["low", "medium", "high"],
    "gpt-image-2.5-sunburst": ["low", "medium", "high", "xhigh", "max"],
}


def is_gpt_pixel_only(model_name):
    return model_name in GPT_PIXEL_ONLY_MODELS


def gpt_ratio_options(model_name):
    if model_name in GPT_PIXEL_ONLY_MODELS:
        return list(GPT_VIP_RATIOS)
    return list(GPT_IMAGE_RATIOS)


def gpt_quality_options(model_name):
    options = GPT_IMAGE_QUALITY_OPTIONS.get(model_name)
    if not options:
        return ["auto"]
    return list(options)


def gpt_pixel_value(ratio, tier):
    """把比例 + 档位换算成 vip 系模型需要的像素值；比例不在表中时原样返回。"""
    if ratio in (None, "", "auto"):
        return "auto"
    entries = GPT_PIXEL_MAP.get(ratio)
    if not entries:
        return ratio
    tier_index = {"1K": 0, "2K": 1, "4K": 2}.get(tier, 0)
    if tier_index >= len(entries):
        tier_index = len(entries) - 1
    return entries[tier_index]


VIP_MODELS = [
    "nano-banana-2-cl",
    "nano-banana-2-2k-cl",
    "nano-banana-2-4k-cl",
    "nano-banana-pro-vip",
    "nano-banana-pro-4k-vip",
    "nano-banana-pro-cl",
    "gpt-image-2-vip",
]

# --- minimax-h3 视频生成（依据 api_docs/minimax-h3接口.md，2026-09-15 版本）---
VIDEO_ASPECT_OPTIONS = ["portrait", "landscape", "square"]
VIDEO_RESOLUTIONS = ["480p", "768p", "1080p"]
VIDEO_MAX_IMAGES = 9
VIDEO_MAX_AUDIOS = 3
VIDEO_MAX_DURATION = 15
# 各分辨率支持的最大时长（1080p 最多 10 秒；同上文档，2026-09-15 版本）
VIDEO_DURATION_LIMITS = {
    "480p": 15,
    "768p": 15,
    "1080p": 10,
}


def video_duration_limit(resolution):
    return VIDEO_DURATION_LIMITS.get(resolution, VIDEO_MAX_DURATION)


NANO_MODELS = set(BANANA_PRO_MODELS)
COMPLETION_MODELS = set(GPT_IMAGE_MODELS)
VIDEO_MODEL_SET = set(VIDEO_MODELS)

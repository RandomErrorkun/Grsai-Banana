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
    # 2026-11-08 官方更新公告新增 2.6 系列（含 sunburst / flare），
    # 基座 gpt-image-2.6 同步上线（接口文档 2026-11-15 版已列出）
    "gpt-image-2.6",
    "gpt-image-2.6-flare",
    "gpt-image-2.6-sunburst",
]

VIDEO_MODELS = [
    "minimax-h3",
    "agnes-video-2.5",
    "wan-3.0",
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


# gpt-image-2 / gpt-image-2.5 / gpt-image-2.6：支持比例或 1K 像素值
# （依据 api_docs/452409160e0.md，2026-11-15 版本）
GPT_IMAGE_RATIOS = [
    "auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3",
    "5:4", "4:5", "21:9", "9:21", "1:2", "2:1",
]

# vip 系模型只支持像素值，比例需按 1K/2K/4K 档位换算成像素（同上文档，2026-11-15 版本）
# 2.6-flare / 2.6-sunburst 与 2.5 同级，同样只接受像素值
GPT_PIXEL_ONLY_MODELS = [
    "gpt-image-2-vip",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
    "gpt-image-2.6-flare",
    "gpt-image-2.6-sunburst",
]
# 2026-11-15 版文档的 background 参数不再列出模型限制；沿用 2.5 系列的口径，
# 2.6 的 flare / sunburst 同级支持 transparent，基座模型不开放
GPT_TRANSPARENT_MODELS = [
    "gpt-image-2-vip",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
    "gpt-image-2.6-flare",
    "gpt-image-2.6-sunburst",
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

# 各模型支持的质量档位（依据 api_docs/452409160e0.md，2026-11-15 版本）
# 注：2026-11-15 版文档同步放宽了 2-vip / 2.5-flare（补 auto 与 low/high 档）；
#     2026-11-08 公告确认 2.6 的 sunburst / flare 不支持 xhigh / max
GPT_IMAGE_QUALITY_OPTIONS = {
    "gpt-image-2": ["auto"],
    "gpt-image-2.5": ["auto"],
    "gpt-image-2-vip": ["auto", "low", "medium", "high"],
    "gpt-image-2.5-flare": ["auto", "low", "medium", "high"],
    "gpt-image-2.5-sunburst": ["auto", "low", "medium", "high", "xhigh", "max"],
    "gpt-image-2.6": ["auto"],
    "gpt-image-2.6-flare": ["auto", "low", "medium", "high"],
    "gpt-image-2.6-sunburst": ["auto", "low", "medium", "high"],
}

# outputFormat 返回图片格式（依据 api_docs/452409160e0.md，2026-11-15 版本 + 2026-11-08 公告）
#   - png 为全局默认；gif 仅 2.6 系列支持，svg 仅基座 gpt-image-2.6 支持
#   - 公告明确「2.6 的 sunburst 和 flare 仅支持 gif 图」，两档锁定为 gif 单选
#   - 未列出的模型不支持该参数，构造请求时不携带
GPT_OUTPUT_FORMAT_OPTIONS = {
    "gpt-image-2.6": ["png", "gif", "svg"],
    "gpt-image-2.6-flare": ["gif"],
    "gpt-image-2.6-sunburst": ["gif"],
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


def gpt_output_format_options(model_name):
    """模型支持的 outputFormat 选项；空列表表示该模型不支持此参数。"""
    return list(GPT_OUTPUT_FORMAT_OPTIONS.get(model_name, []))


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

# --- 视频生成模型参数 ---
# minimax-h3（依据 api_docs/minimax-h3接口.md，2026-09-15 版本）
MINIMAX_VIDEO_ASPECT_OPTIONS = ["portrait", "landscape", "square"]
MINIMAX_VIDEO_RESOLUTIONS = ["480p", "768p", "1080p"]
MINIMAX_VIDEO_MAX_IMAGES = 9
MINIMAX_VIDEO_MAX_AUDIOS = 3
MINIMAX_VIDEO_MIN_DURATION = 1
MINIMAX_VIDEO_MAX_DURATION = 15
# 各分辨率支持的最大时长（1080p 最多 10 秒；同上文档，2026-09-15 版本）
MINIMAX_VIDEO_DURATION_LIMITS = {
    "480p": 15,
    "768p": 15,
    "1080p": 10,
}

# agnes-video-2.5（依据 api_docs/agnes-video接口.md，2026-10-17 版本）
# 支持对白/声音设计提示（口型同步），时长固定 4~12 秒，与分辨率无关
# 首尾帧：接口文档同样提供 firstFrame / lastFrame（与 images、audios 互斥）
AGNES_VIDEO_ASPECT_OPTIONS = ["16:9", "9:16", "21:9", "4:3", "1:1", "3:4"]
AGNES_VIDEO_RESOLUTIONS = ["720p", "1080p", "2k"]
AGNES_VIDEO_MAX_IMAGES = 5
AGNES_VIDEO_MAX_AUDIOS = 3
AGNES_VIDEO_MIN_DURATION = 4
AGNES_VIDEO_MAX_DURATION = 12

# wan-3.0（依据 api_docs/wan-video接口.md，2026-11-05 版本）
# 参考图最多 10 张；参考音频最多 5 段、每段最长 15 秒（由服务端校验）；
# 首尾帧 firstFrame / lastFrame 与 images、audios 参数互斥，可只给其中一帧
WAN_VIDEO_ASPECT_OPTIONS = ["16:9", "9:16", "21:9", "4:3", "1:1", "3:4"]
WAN_VIDEO_RESOLUTIONS = ["480p", "720p", "1080p"]
WAN_VIDEO_MAX_IMAGES = 10
WAN_VIDEO_MAX_AUDIOS = 5
WAN_VIDEO_MIN_DURATION = 2
WAN_VIDEO_MAX_DURATION = 30

# 旧常量名保留给既有引用（默认指向 minimax-h3）。
# 注意：VIDEO_MAX_DURATION（15 秒）是 minimax 时代的全局时长上限，wan-3.0 已支持
# 30 秒，时长钳制一律改按各模型 spec 的 min/max_duration 处理，勿再叠加该全局值。
VIDEO_ASPECT_OPTIONS = MINIMAX_VIDEO_ASPECT_OPTIONS
VIDEO_RESOLUTIONS = MINIMAX_VIDEO_RESOLUTIONS
VIDEO_MAX_IMAGES = MINIMAX_VIDEO_MAX_IMAGES
VIDEO_MAX_AUDIOS = MINIMAX_VIDEO_MAX_AUDIOS
VIDEO_MAX_DURATION = MINIMAX_VIDEO_MAX_DURATION
VIDEO_DURATION_LIMITS = MINIMAX_VIDEO_DURATION_LIMITS

# 各视频模型的可选参数集（UI 与请求构造共用同一份配置）
# supports_frames：接口是否提供 firstFrame / lastFrame（与 images、audios 互斥）
# max_videos：参考视频上限。0 表示暂不支持——wan-3.0 官方公告预告日后将支持上传
#             参考视频，接口参数尚未开放；届时仅需在此置为正数并补充 UI 入口，
#             请求 / 任务 / 历史链路（ref_videos）已预留贯通
VIDEO_MODEL_SPECS = {
    "minimax-h3": {
        "aspects": MINIMAX_VIDEO_ASPECT_OPTIONS,
        "resolutions": MINIMAX_VIDEO_RESOLUTIONS,
        "max_images": MINIMAX_VIDEO_MAX_IMAGES,
        "max_audios": MINIMAX_VIDEO_MAX_AUDIOS,
        "min_duration": MINIMAX_VIDEO_MIN_DURATION,
        "max_duration": MINIMAX_VIDEO_MAX_DURATION,
        "duration_limits": MINIMAX_VIDEO_DURATION_LIMITS,
        "default_aspect": "landscape",
        "default_resolution": "480p",
        "supports_frames": False,
        "max_videos": 0,
    },
    "agnes-video-2.5": {
        "aspects": AGNES_VIDEO_ASPECT_OPTIONS,
        "resolutions": AGNES_VIDEO_RESOLUTIONS,
        "max_images": AGNES_VIDEO_MAX_IMAGES,
        "max_audios": AGNES_VIDEO_MAX_AUDIOS,
        "min_duration": AGNES_VIDEO_MIN_DURATION,
        "max_duration": AGNES_VIDEO_MAX_DURATION,
        "duration_limits": {r: AGNES_VIDEO_MAX_DURATION for r in AGNES_VIDEO_RESOLUTIONS},
        "default_aspect": "16:9",
        "default_resolution": "720p",
        "supports_frames": True,
        "max_videos": 0,
    },
    "wan-3.0": {
        "aspects": WAN_VIDEO_ASPECT_OPTIONS,
        "resolutions": WAN_VIDEO_RESOLUTIONS,
        "max_images": WAN_VIDEO_MAX_IMAGES,
        "max_audios": WAN_VIDEO_MAX_AUDIOS,
        "min_duration": WAN_VIDEO_MIN_DURATION,
        "max_duration": WAN_VIDEO_MAX_DURATION,
        "duration_limits": {r: WAN_VIDEO_MAX_DURATION for r in WAN_VIDEO_RESOLUTIONS},
        "default_aspect": "16:9",
        "default_resolution": "720p",
        "supports_frames": True,
        "max_videos": 0,
    },
}


def _video_spec(model):
    return VIDEO_MODEL_SPECS.get(model) or VIDEO_MODEL_SPECS["minimax-h3"]


def video_aspect_options(model):
    return list(_video_spec(model)["aspects"])


def video_resolutions(model):
    return list(_video_spec(model)["resolutions"])


def video_max_images(model):
    return _video_spec(model)["max_images"]


def video_max_audios(model):
    return _video_spec(model)["max_audios"]


def video_duration_bounds(model):
    """返回 (min, max) 全局时长边界（未按分辨率收窄）。"""
    spec = _video_spec(model)
    return spec["min_duration"], spec["max_duration"]


def video_default_aspect(model):
    return _video_spec(model)["default_aspect"]


def video_default_resolution(model):
    return _video_spec(model)["default_resolution"]


def video_duration_limit(model, resolution):
    """指定模型 + 分辨率下的最大时长。"""
    limits = _video_spec(model)["duration_limits"]
    max_duration = _video_spec(model)["max_duration"]
    return limits.get(resolution, max_duration)


def video_supports_frames(model):
    """模型是否支持首尾帧（firstFrame / lastFrame，与 images、audios 互斥）。"""
    return bool(_video_spec(model).get("supports_frames"))


def video_max_videos(model):
    """参考视频上限；0 表示该模型暂不支持参考视频（接口参数未开放）。"""
    return int(_video_spec(model).get("max_videos", 0))


NANO_MODELS = set(BANANA_PRO_MODELS)
COMPLETION_MODELS = set(GPT_IMAGE_MODELS)
VIDEO_MODEL_SET = set(VIDEO_MODELS)

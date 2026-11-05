import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QApplication, QStackedWidget
from qfluentwidgets import (CardWidget, PrimaryPushButton, ComboBox, CaptionLabel,
                            InfoBar, InfoBarPosition, CheckBox, Slider, SegmentedWidget,
                            TransparentToolButton, FluentIcon, StrongBodyLabel, BodyLabel,
                            SpinBox, LineEdit, isDarkTheme, qconfig)

from core.config import cfg
from core.i18n import tr
from core.model_catalog import (
    VIDEO_MODELS,
    video_aspect_options,
    video_resolutions,
    video_max_images,
    video_max_audios,
    video_duration_bounds,
    video_duration_limit,
    video_default_aspect,
    video_default_resolution,
    video_supports_frames,
)
from core.task_manager import task_manager
from ui.components.prompt_widget import PromptWidget
from ui.components.image_drop_area import ImageDropArea
from ui.components.audio_drop_area import AudioDropArea
from ui.components.task_widget import TaskWidget, TaskListWidget

ASPECT_LABEL_KEYS = {
    "portrait": "video.aspect.portrait",
    "landscape": "video.aspect.landscape",
    "square": "video.aspect.square",
}

HINT_KEYS = {
    "minimax-h3": "video.hint_minimax",
    "agnes-video-2.5": "video.hint_agnes",
    "wan-3.0": "video.hint_wan",
}

# 各模型的参数记忆键（minimax 沿用旧键，老用户设置不丢）
VIDEO_MODEL_CONFIG_KEYS = {
    "minimax-h3": ("video_aspect_ratio", "video_resolution", "video_duration"),
    "agnes-video-2.5": ("agnes_video_aspect_ratio", "agnes_video_resolution", "agnes_video_duration"),
    "wan-3.0": ("wan_video_aspect_ratio", "wan_video_resolution", "wan_video_duration"),
}

# 素材模式：参考图/音频 与 首尾帧 互斥（依据 wan-video / agnes-video 接口文档）
REF_MODE_REFS = "refs"
REF_MODE_FRAMES = "frames"


class VideoPage(QWidget):
    """视频生成页面（minimax-h3 / agnes-video-2.5 / wan-3.0），布局与功能复用图像生成页面。

    支持首尾帧的模型（wan-3.0 / agnes-video-2.5）在参考素材区提供两种互斥模式：
    参考图+参考音频（images/audios）或 首帧+尾帧（firstFrame/lastFrame），
    由接口约束决定——两套参数不能同时提交。
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("VideoPage")
        self.task_counter = 0
        # 当前是否处于首尾帧素材模式（仅对支持 firstFrame/lastFrame 的模型生效）
        self._ref_mode_frames = False
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left Side (2/3 width)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # --- Top Section: Settings Card ---
        settings_container = QWidget()
        settings_layout_v = QVBoxLayout(settings_container)
        settings_layout_v.setContentsMargins(0, 0, 0, 0)
        settings_layout_v.setSpacing(10)

        # 1. Header tabs spacer (与生成页视觉对齐)
        self.header_tabs = SegmentedWidget()
        self.header_tabs.addItem("video", tr("nav.video"))
        self.header_tabs.setCurrentItem("video")
        self.header_tabs.setEnabled(False)
        settings_layout_v.addWidget(self.header_tabs)

        # 2. Settings Card
        self.settings_card = CardWidget()
        self.update_card_style(self.settings_card)
        qconfig.themeChanged.connect(lambda: self.update_card_style(self.settings_card))
        settings_inner = QVBoxLayout(self.settings_card)

        # Model
        self.model_caption = CaptionLabel(tr("video.model"))
        settings_inner.addWidget(self.model_caption)
        self.model_combo = ComboBox()
        self.model_combo.addItems(VIDEO_MODELS)
        settings_inner.addWidget(self.model_combo)

        # Aspect Ratio / Resolution（双列，压缩纵向高度；选项随模型联动填充）
        param_row_1 = QHBoxLayout()
        param_row_1.setSpacing(12)

        self.aspect_label = CaptionLabel(tr("video.aspect_ratio"))
        param_row_1.addWidget(self.aspect_label)
        self.aspect_combo = ComboBox()
        param_row_1.addWidget(self.aspect_combo, 1)

        self.resolution_label = CaptionLabel(tr("video.resolution"))
        param_row_1.addWidget(self.resolution_label)
        self.resolution_combo = ComboBox()
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        param_row_1.addWidget(self.resolution_combo, 1)
        settings_inner.addLayout(param_row_1)

        # Duration / Seed（双列）
        param_row_2 = QHBoxLayout()
        param_row_2.setSpacing(12)

        self.duration_label = CaptionLabel(tr("video.duration"))
        param_row_2.addWidget(self.duration_label)
        self.duration_spin = SpinBox()
        self.duration_spin.setRange(1, 15)
        param_row_2.addWidget(self.duration_spin, 1)

        self.seed_label = CaptionLabel(tr("video.seed"))
        param_row_2.addWidget(self.seed_label)
        self.seed_edit = LineEdit()
        self.seed_edit.setPlaceholderText(tr("video.seed_placeholder"))
        param_row_2.addWidget(self.seed_edit, 1)
        settings_inner.addLayout(param_row_2)

        # Auto Retry and Parallel Tasks
        retry_parallel_layout = QHBoxLayout()

        self.auto_retry_cb = CheckBox(tr("generator.auto_retry"))
        self.auto_retry_cb.setChecked(cfg.get("auto_retry_on_failure", False))
        retry_parallel_layout.addWidget(self.auto_retry_cb)

        retry_parallel_layout.addStretch()

        self.parallel_label = BodyLabel(tr("generator.parallel_tasks"))
        retry_parallel_layout.addWidget(self.parallel_label)

        self.parallel_slider = Slider(Qt.Horizontal)
        self.parallel_slider.setMinimum(1)
        self.parallel_slider.setMaximum(10)
        self.parallel_slider.setValue(cfg.get("video_parallel_tasks", 1))
        self.parallel_slider.setFixedWidth(200)
        self.parallel_slider.setTickPosition(Slider.TicksBelow)
        self.parallel_slider.setTickInterval(1)
        retry_parallel_layout.addWidget(self.parallel_slider)

        self.parallel_value_label = QLabel(str(cfg.get("video_parallel_tasks", 1)))
        self.parallel_value_label.setFixedWidth(24)
        self.update_parallel_value_label_color()
        self.parallel_slider.valueChanged.connect(lambda v: self.parallel_value_label.setText(str(v)))
        retry_parallel_layout.addWidget(self.parallel_value_label)

        settings_inner.addLayout(retry_parallel_layout)

        # Hint（文案随模型联动更新）
        self.hint_label = CaptionLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setMaximumHeight(64)
        settings_inner.addWidget(self.hint_label)

        settings_layout_v.addWidget(self.settings_card)

        left_layout.addWidget(settings_container)

        # --- Middle Section: References & Prompt ---
        middle_split = QWidget()
        middle_layout = QHBoxLayout(middle_split)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(15)

        # Reference column: 素材模式切换（参考图/音频 ↔ 首尾帧，互斥）+ 两种素材面板
        ref_column = QWidget()
        ref_column_layout = QVBoxLayout(ref_column)
        ref_column_layout.setContentsMargins(0, 0, 0, 0)
        ref_column_layout.setSpacing(5)

        # 模式切换（仅支持首尾帧的模型可见；wan-3.0 / agnes-video-2.5）
        self.ref_mode_tabs = SegmentedWidget()
        self.ref_mode_tabs.addItem(REF_MODE_REFS, tr("video.ref_mode.refs"))
        self.ref_mode_tabs.addItem(REF_MODE_FRAMES, tr("video.ref_mode.frames"))
        self.ref_mode_tabs.currentItemChanged.connect(self.on_ref_mode_changed)
        self.ref_mode_tabs.hide()
        ref_column_layout.addWidget(self.ref_mode_tabs)

        self.ref_mode_stack = QStackedWidget()
        ref_column_layout.addWidget(self.ref_mode_stack, 1)

        # Page 0: 参考图 + 参考音频（images / audios）
        ref_container = QWidget()
        ref_container_layout = QVBoxLayout(ref_container)
        ref_container_layout.setContentsMargins(0, 0, 0, 0)
        ref_container_layout.setSpacing(5)

        # Images header
        img_header_layout = QHBoxLayout()
        img_header_layout.setContentsMargins(0, 0, 0, 0)
        self.ref_images_label = StrongBodyLabel(tr("video.reference_images"))
        img_header_layout.addWidget(self.ref_images_label)
        img_header_layout.addStretch()

        img_paste_btn = TransparentToolButton(FluentIcon.PASTE)
        img_paste_btn.setToolTip(tr("drop.tooltip.paste"))
        img_paste_btn.clicked.connect(self.on_image_paste)
        img_header_layout.addWidget(img_paste_btn)

        img_clear_btn = TransparentToolButton(FluentIcon.DELETE)
        img_clear_btn.setToolTip(tr("drop.tooltip.clear"))
        img_clear_btn.clicked.connect(self.on_image_clear)
        img_header_layout.addWidget(img_clear_btn)

        ref_container_layout.addLayout(img_header_layout)

        self.drop_area = ImageDropArea(max_images=max(video_max_images(m) for m in VIDEO_MODELS))
        self.drop_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ref_container_layout.addWidget(self.drop_area, 2)

        # Audios（紧凑文件表格：文件名 / 时长 / 播放·停止·删除）
        audio_header_layout = QHBoxLayout()
        audio_header_layout.setContentsMargins(0, 0, 0, 0)
        self.ref_audios_label = StrongBodyLabel(tr("video.reference_audios"))
        audio_header_layout.addWidget(self.ref_audios_label)
        audio_header_layout.addStretch()

        audio_add_btn = TransparentToolButton(FluentIcon.ADD)
        audio_add_btn.setToolTip(tr("audio.tooltip.add"))
        audio_add_btn.clicked.connect(self.on_audio_add)
        audio_header_layout.addWidget(audio_add_btn)

        audio_clear_btn = TransparentToolButton(FluentIcon.DELETE)
        audio_clear_btn.setToolTip(tr("drop.tooltip.clear"))
        audio_clear_btn.clicked.connect(self.on_audio_clear)
        audio_header_layout.addWidget(audio_clear_btn)

        ref_container_layout.addLayout(audio_header_layout)

        self.audio_area = AudioDropArea(max_files=max(video_max_audios(m) for m in VIDEO_MODELS))
        ref_container_layout.addWidget(self.audio_area)

        self.ref_mode_stack.addWidget(ref_container)

        # Page 1: 首帧 / 尾帧（firstFrame / lastFrame，与 images、audios 互斥）
        frames_container = QWidget()
        frames_layout = QVBoxLayout(frames_container)
        frames_layout.setContentsMargins(0, 0, 0, 0)
        frames_layout.setSpacing(5)

        self.first_frame_area = self._build_frame_slot(
            frames_layout, "video.first_frame", "video.first_frame_placeholder",
            self.on_first_frame_paste, self.on_first_frame_clear,
        )
        self.last_frame_area = self._build_frame_slot(
            frames_layout, "video.last_frame", "video.last_frame_placeholder",
            self.on_last_frame_paste, self.on_last_frame_clear,
        )

        # 参考视频预留位：wan-3.0 官方公告预告将支持上传参考视频，接口参数暂未开放；
        # 上游开放后在 VIDEO_MODEL_SPECS 中把 wan-3.0 的 max_videos 置为正数，
        # 并在此处追加视频素材槽位（请求 / 任务 / 历史链路已按 ref_videos 贯通）

        self.ref_mode_stack.addWidget(frames_container)

        middle_layout.addWidget(ref_column, 1)

        # Prompt Widget
        self.prompt_widget = PromptWidget()
        self.prompt_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        middle_layout.addWidget(self.prompt_widget, 1)

        left_layout.addWidget(middle_split, 1)

        # --- Bottom Section: Generate Button ---
        self.gen_btn = PrimaryPushButton(tr("video.generate"))
        self.gen_btn.clicked.connect(self.on_generate)
        self.gen_btn.setFixedHeight(45)
        left_layout.addWidget(self.gen_btn)

        main_layout.addWidget(left_panel, 2)

        # Right Side (1/3 width) - Task List
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Add a dummy widget to match the tabs spacing
        self.task_list_tabs_spacer = SegmentedWidget()
        self.task_list_tabs_spacer.addItem("task_list", tr("video.task_list"))
        self.task_list_tabs_spacer.setCurrentItem("task_list")
        self.task_list_tabs_spacer.setEnabled(False)
        right_layout.addWidget(self.task_list_tabs_spacer)

        self.task_list_widget = TaskListWidget()
        right_layout.addWidget(self.task_list_widget, 1)

        main_layout.addWidget(right_panel, 1)

        # 按上次使用的模型初始化联动选项（组合框文本未变化时不会触发信号，这里显式应用一次）
        initial_model = cfg.get("video_last_model", VIDEO_MODELS[0])
        if initial_model not in VIDEO_MODELS:
            initial_model = VIDEO_MODELS[0]
        self.model_combo.setCurrentText(initial_model)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self._apply_model_options(initial_model)

    def _build_frame_slot(self, parent_layout, label_key, placeholder_key, paste_handler, clear_handler):
        """构建单个首帧/尾帧槽位：标题行（粘贴/清除按钮）+ 单图拖拽区。"""
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(StrongBodyLabel(tr(label_key)))
        header_layout.addStretch()

        paste_btn = TransparentToolButton(FluentIcon.PASTE)
        paste_btn.setToolTip(tr("drop.tooltip.paste"))
        paste_btn.clicked.connect(paste_handler)
        header_layout.addWidget(paste_btn)

        clear_btn = TransparentToolButton(FluentIcon.DELETE)
        clear_btn.setToolTip(tr("drop.tooltip.clear"))
        clear_btn.clicked.connect(clear_handler)
        header_layout.addWidget(clear_btn)

        parent_layout.addLayout(header_layout)

        frame_area = ImageDropArea(max_images=1, placeholder_key=placeholder_key)
        frame_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        parent_layout.addWidget(frame_area, 1)
        return frame_area

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            if mime_data.hasImage() or mime_data.hasUrls():
                self._paste_target().paste_from_clipboard()

    def _paste_target(self):
        """Ctrl+V 的目标素材区：首尾帧模式下优先粘贴到空帧槽位。"""
        if self._frames_mode_active():
            if not self.first_frame_area.image_paths:
                return self.first_frame_area
            if not self.last_frame_area.image_paths:
                return self.last_frame_area
            return self.first_frame_area
        return self.drop_area

    # --- 素材模式（参考图/音频 ↔ 首尾帧，二者互斥） ---

    def _model_supports_frames(self):
        return video_supports_frames(self._current_model())

    def _frames_mode_active(self):
        return self._ref_mode_frames and self._model_supports_frames()

    def on_ref_mode_changed(self, route_key):
        self._set_ref_mode(route_key == REF_MODE_FRAMES, persist=True)

    def _set_ref_mode(self, frames, persist=False):
        """切换素材面板；persist=False 用于模型不支持首尾帧时的临时回退，不覆盖用户偏好。"""
        self._ref_mode_frames = bool(frames)
        self.ref_mode_stack.setCurrentIndex(1 if self._ref_mode_frames else 0)
        if persist:
            cfg.set("video_frames_mode", self._ref_mode_frames)

    def update_parallel_value_label_color(self):
        """Update the color of the parallel value label based on theme"""
        if isDarkTheme():
            self.parallel_value_label.setStyleSheet("color: #ffffff;")
        else:
            self.parallel_value_label.setStyleSheet("color: #000000;")

    def update_card_style(self, card_widget):
        """Unify card background color for both light and dark themes"""
        if isDarkTheme():
            bg_color = "rgba(255, 255, 255, 0.06)"
        else:
            bg_color = "rgb(255, 255, 255)"
        card_widget.setStyleSheet(f"CardWidget {{ background-color: {bg_color}; }}")

    def _current_model(self):
        return self.model_combo.currentText() or VIDEO_MODELS[0]

    def _config_keys(self, model):
        return VIDEO_MODEL_CONFIG_KEYS.get(model) or VIDEO_MODEL_CONFIG_KEYS[VIDEO_MODELS[0]]

    def _apply_model_options(self, model):
        """按模型重刷比例/分辨率选项、时长范围、参考图上限与提示文案，并恢复该模型的上次参数。"""
        aspects = video_aspect_options(model)
        resolutions = video_resolutions(model)
        min_duration, max_duration = video_duration_bounds(model)
        aspect_key, resolution_key, duration_key = self._config_keys(model)

        self.aspect_combo.blockSignals(True)
        self.aspect_combo.clear()
        self.aspect_combo.addItems([tr(ASPECT_LABEL_KEYS.get(value, value)) for value in aspects])
        saved_aspect = cfg.get(aspect_key, video_default_aspect(model))
        if saved_aspect not in aspects:
            saved_aspect = video_default_aspect(model)
        self.aspect_combo.setCurrentText(tr(ASPECT_LABEL_KEYS.get(saved_aspect, saved_aspect)))
        self.aspect_combo.blockSignals(False)

        self.resolution_combo.blockSignals(True)
        self.resolution_combo.clear()
        self.resolution_combo.addItems(resolutions)
        saved_resolution = cfg.get(resolution_key, video_default_resolution(model))
        if saved_resolution not in resolutions:
            saved_resolution = video_default_resolution(model)
        self.resolution_combo.setCurrentText(saved_resolution)
        self.resolution_combo.blockSignals(False)

        self.duration_spin.blockSignals(True)
        self.duration_spin.setRange(min_duration, max_duration)
        try:
            saved_duration = int(cfg.get(duration_key, 5))
        except (TypeError, ValueError):
            saved_duration = 5
        saved_duration = max(min_duration, min(saved_duration, self._duration_limit(), max_duration))
        self.duration_spin.setValue(saved_duration)
        self.duration_spin.blockSignals(False)

        self.drop_area.MAX_IMAGES = video_max_images(model)
        self.drop_area.update_texts()
        self.hint_label.setText(tr(HINT_KEYS.get(model, HINT_KEYS[VIDEO_MODELS[0]])))

        # 首尾帧模式仅对支持的模型开放；切换到不支持的模型时临时回退到参考图模式
        supports_frames = video_supports_frames(model)
        self.ref_mode_tabs.setVisible(supports_frames)
        use_frames = supports_frames and bool(cfg.get("video_frames_mode", False))
        self.ref_mode_tabs.blockSignals(True)
        self.ref_mode_tabs.setCurrentItem(REF_MODE_FRAMES if use_frames else REF_MODE_REFS)
        self.ref_mode_tabs.blockSignals(False)
        self._set_ref_mode(use_frames)

    def on_model_changed(self, model):
        self._apply_model_options(model)

    def _aspect_value(self):
        model = self._current_model()
        current_text = self.aspect_combo.currentText()
        for value in video_aspect_options(model):
            if tr(ASPECT_LABEL_KEYS.get(value, value)) == current_text:
                return value
        return video_default_aspect(model)

    def _set_aspect_by_value(self, value):
        model = self._current_model()
        if value not in video_aspect_options(model):
            value = video_default_aspect(model)
        self.aspect_combo.setCurrentText(tr(ASPECT_LABEL_KEYS.get(value, value)))

    def _duration_limit(self):
        return video_duration_limit(self._current_model(), self.resolution_combo.currentText())

    def on_resolution_changed(self, _text):
        limit = self._duration_limit()
        if self.duration_spin.value() > limit:
            self.duration_spin.setValue(limit)
            InfoBar.info(
                title=tr("common.note"),
                content=tr("video.duration_capped", max=limit),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
            )

    def update_text_formatting(self):
        self.prompt_widget.update_text_formatting()

    def on_generate(self):
        prompt = self.prompt_widget.get_prompt()
        if not prompt:
            InfoBar.warning(title=tr("common.warning"), content=tr("video.enter_prompt_warning"), parent=self, position=InfoBarPosition.TOP_RIGHT)
            return

        seed_text = self.seed_edit.text().strip()
        seed = None
        if seed_text:
            try:
                seed = int(seed_text)
            except ValueError:
                InfoBar.warning(title=tr("common.warning"), content=tr("video.seed_invalid"), parent=self, position=InfoBarPosition.TOP_RIGHT)
                return

        model = self._current_model()
        aspect = self._aspect_value()
        resolution = self.resolution_combo.currentText()
        min_duration, max_duration = video_duration_bounds(model)
        duration = max(min_duration, min(self.duration_spin.value(), self._duration_limit()))

        aspect_key, resolution_key, duration_key = self._config_keys(model)
        cfg.set(aspect_key, aspect)
        cfg.set(resolution_key, resolution)
        cfg.set(duration_key, duration)
        cfg.set("video_last_model", model)

        parallel_count = self.parallel_slider.value()
        cfg.set("auto_retry_on_failure", self.auto_retry_cb.isChecked())
        cfg.set("video_parallel_tasks", parallel_count)

        # 素材模式互斥：首尾帧模式只收集 firstFrame/lastFrame（二者至少其一），
        # 参考图模式只收集 images/audios；两套参数不会同时出现在请求里
        first_frame = last_frame = None
        if self._frames_mode_active():
            frame_paths = self.first_frame_area.image_paths
            if frame_paths and os.path.isfile(frame_paths[0]):
                first_frame = frame_paths[0]
            frame_paths = self.last_frame_area.image_paths
            if frame_paths and os.path.isfile(frame_paths[0]):
                last_frame = frame_paths[0]
            if not first_frame and not last_frame:
                InfoBar.warning(title=tr("common.warning"), content=tr("video.frames_empty_warning"),
                                parent=self, position=InfoBarPosition.TOP_RIGHT)
                return
            ref_urls = []
            ref_audios = []
        else:
            ref_urls = [p for p in self.drop_area.image_paths if os.path.isfile(p)][:video_max_images(model)]
            ref_audios = [p for p in self.audio_area.audio_paths if os.path.isfile(p)][:video_max_audios(model)]

        params = {
            "model": model,
            "ratio": aspect,
            "size": resolution,
            "ref_urls": ref_urls,
            "ref_audios": ref_audios,
            "first_frame": first_frame,
            "last_frame": last_frame,
            "duration": duration,
            "seed": seed,
            "variants": 1,
            "media_type": "video",
        }

        for _ in range(parallel_count):
            self.create_task(prompt, params)

    def create_task(self, prompt, params):
        self.task_counter += 1
        task_widget = TaskWidget(self.task_counter, prompt, params)
        task_widget.auto_retry = self.auto_retry_cb.isChecked()

        task_widget.retry_requested.connect(self.retry_task)
        task_widget.regenerate_requested.connect(self.regenerate_task)

        self.task_list_widget.add_task(task_widget)
        self.start_worker(task_widget)

    def start_worker(self, task_widget):
        try:
            params = task_widget.params
            worker = task_manager.create_worker(
                task_widget.prompt,
                params["model"],
                params["ratio"],
                params["size"],
                params["ref_urls"],
                variants=params.get("variants", 1),
                duration=params.get("duration"),
                seed=params.get("seed"),
                ref_audios=params.get("ref_audios"),
                first_frame=params.get("first_frame"),
                last_frame=params.get("last_frame"),
                ref_videos=params.get("ref_videos"),
            )

            task_widget.progress_ring.show()
            task_widget.progress_ring.setValue(0)
            task_widget.status_label.setText(f"Attempt {task_widget.attempt_count + 1}: Starting...")

            worker.progress_signal.connect(task_widget.update_progress)
            worker.finished_signal.connect(lambda s, r, m: self.on_worker_finished(task_widget, s, r, m))
            worker.finished.connect(lambda: self.cleanup_worker(task_widget))

            task_manager.register_worker(task_widget, worker)
            worker.start()
        except Exception as e:
            print(f"[VideoPage] Error in start_worker: {e}")

    def on_worker_finished(self, task_widget, success, result, msg):
        if success:
            task_widget.set_success(result)
        else:
            task_widget.set_failed(result, msg)

    def cleanup_worker(self, task_widget):
        task_manager.unregister_worker(task_widget)

    def retry_task(self, task_widget):
        self.start_worker(task_widget)

    def regenerate_task(self, task_widget):
        self.create_task(task_widget.prompt, task_widget.params.copy())

    def apply_history_task(self, task_data):
        """从历史记录恢复视频任务参数（选项集随时切换的模型联动）"""
        self.prompt_widget.set_prompt(task_data.get("prompt", ""))

        model = task_data.get("model", VIDEO_MODELS[0])
        if self.model_combo.findText(model) < 0:
            model = VIDEO_MODELS[0]
        # setCurrentText 与当前值相同时不触发信号，这里统一显式重刷一次联动选项
        self.model_combo.setCurrentText(model)
        self._apply_model_options(model)

        self._set_aspect_by_value(task_data.get("aspect_ratio") or video_default_aspect(model))

        resolution = task_data.get("image_size") or video_default_resolution(model)
        if self.resolution_combo.findText(resolution) >= 0:
            self.resolution_combo.setCurrentText(resolution)

        min_duration, max_duration = video_duration_bounds(model)
        duration = task_data.get("duration")
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            _, _, duration_key = self._config_keys(model)
            duration = cfg.get(duration_key, 5)
        self.duration_spin.setValue(max(min_duration, min(duration, max_duration)))

        seed = task_data.get("seed")
        self.seed_edit.setText(str(int(seed)) if seed not in (None, "") else "")

        self.drop_area.clear_images()
        ref_images = task_data.get("ref_images")
        if isinstance(ref_images, str):
            ref_images = [ref_images]
        for img_path in ref_images or []:
            self.drop_area.add_image(img_path)

        self.audio_area.clear_audios()
        ref_audios = task_data.get("ref_audios")
        if isinstance(ref_audios, str):
            ref_audios = [ref_audios]
        if ref_audios:
            self.audio_area.add_files(ref_audios, show_limit_warning=False)

        # 首尾帧任务恢复：任一帧存在即切到首尾帧模式（参考图 / 音频此时为空，
        # 与接口互斥约束一致）
        first_frame = task_data.get("first_frame")
        last_frame = task_data.get("last_frame")
        self.first_frame_area.clear_images()
        self.last_frame_area.clear_images()
        if video_supports_frames(model):
            if first_frame and os.path.isfile(first_frame):
                self.first_frame_area.add_image(first_frame)
            if last_frame and os.path.isfile(last_frame):
                self.last_frame_area.add_image(last_frame)
            if first_frame or last_frame:
                self.ref_mode_tabs.setCurrentItem(REF_MODE_FRAMES)

    def on_image_paste(self):
        self.drop_area.paste_from_clipboard()

    def on_image_clear(self):
        self.drop_area.clear_images()

    def on_first_frame_paste(self):
        self.first_frame_area.paste_from_clipboard()

    def on_first_frame_clear(self):
        self.first_frame_area.clear_images()

    def on_last_frame_paste(self):
        self.last_frame_area.paste_from_clipboard()

    def on_last_frame_clear(self):
        self.last_frame_area.clear_images()

    def on_audio_add(self):
        self.audio_area.open_file_dialog()

    def on_audio_clear(self):
        self.audio_area.clear_audios()

    def stop_all_workers(self):
        task_manager.stop_all_workers()

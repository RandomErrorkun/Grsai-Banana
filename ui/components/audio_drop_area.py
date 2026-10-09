import os
from collections import deque

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QFrame, QHBoxLayout,
                               QHeaderView, QTableWidgetItem, QVBoxLayout, QWidget)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from qfluentwidgets import (TransparentPushButton, TransparentToolButton, TableWidget,
                            InfoBar, InfoBarPosition, FluentIcon, isDarkTheme, qconfig)

from core.i18n import tr


def _format_duration(ms):
    if not ms or ms <= 0:
        return "--:--"
    total_seconds = int(round(ms / 1000))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


class AudioDropArea(QFrame):
    """紧凑的参考音频表格：文件名 / 时长 / 播放·暂停、停止、删除。

    所有行共用一个 QMediaPlayer（互斥播放）；时长通过加载媒体后的
    durationChanged 信号探测，探测失败显示 --:--。
    """

    SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")

    def __init__(self, parent=None, max_files=3):
        super().__init__(parent)
        self.max_files = int(max_files)
        self.audio_paths = []
        self._durations = {}      # path -> duration ms
        self._play_buttons = {}   # path -> play/pause button
        self._probe_queue = deque()
        self._probing = False
        self._playing_path = None

        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 空状态：一行细高的“点击添加”提示按钮
        self.add_btn = TransparentPushButton(FluentIcon.MUSIC, tr("audio.add_hint", max=self.max_files))
        self.add_btn.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.add_btn)

        # 文件表格
        self.table = TableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            tr("audio.column.name"),
            tr("audio.column.duration"),
            tr("audio.column.actions"),
        ])
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().resizeSection(1, 64)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().resizeSection(2, 118)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setWordWrap(False)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setFixedHeight(34 + 30 * self.max_files + 2)
        layout.addWidget(self.table)

        self.update_style()
        qconfig.themeChanged.connect(self.update_style)
        self._update_ui_state()

        # 共享播放器
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.errorOccurred.connect(self._on_player_error)

        # 单个文件的时长探测超时兜底（异常格式可能永远不发 durationChanged）
        self._probe_timer = QTimer(self)
        self._probe_timer.setSingleShot(True)
        self._probe_timer.timeout.connect(self._on_probe_timeout)

    def update_style(self):
        if isDarkTheme():
            bg_color = "rgba(255, 255, 255, 0.06)"
            border_color = "rgba(255, 255, 255, 0.1)"
        else:
            bg_color = "rgb(255, 255, 255)"
            border_color = "rgba(0, 0, 0, 0.12)"

        self.setStyleSheet(
            f"""
            QFrame {{
                border: 1px solid {border_color};
                border-radius: 6px;
                background-color: {bg_color};
            }}
            """
        )

    # --- 文件管理 ---

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.add_files(paths, show_limit_warning=True)
        event.acceptProposedAction()

    def open_file_dialog(self):
        fnames, _ = QFileDialog.getOpenFileNames(
            self, tr("audio.dialog.open_files"), "", tr("audio.dialog.filter")
        )
        if fnames:
            self.add_files(fnames, show_limit_warning=True)

    def _is_supported_audio(self, path):
        return bool(path) and path.lower().endswith(self.SUPPORTED_EXTENSIONS)

    def add_files(self, paths, show_limit_warning=False):
        if not paths:
            return 0

        available_slots = max(self.max_files - len(self.audio_paths), 0)
        if available_slots == 0:
            if show_limit_warning:
                InfoBar.warning(
                    title=tr("common.limit_reached"),
                    content=tr("audio.msg.limit_reached", max=self.max_files),
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                )
            return 0

        valid_new_paths = []
        for raw_path in paths:
            if not raw_path:
                continue
            # QFileDialog/拖拽返回的路径可能是正斜杠，统一 normpath，
            # 否则与 QUrl.toLocalFile()+normpath 探测结果的键不匹配
            path = os.path.normpath(str(raw_path))
            if not self._is_supported_audio(path):
                continue
            if path in self.audio_paths or path in valid_new_paths:
                continue
            valid_new_paths.append(path)

        if not valid_new_paths:
            return 0

        overflow_count = max(len(valid_new_paths) - available_slots, 0)
        paths_to_add = valid_new_paths[:available_slots]

        self.audio_paths.extend(paths_to_add)
        self._refresh_table()

        for path in paths_to_add:
            self._queue_probe(path)

        if overflow_count > 0 and show_limit_warning:
            InfoBar.warning(
                title=tr("common.limit_reached"),
                content=tr("audio.msg.limit_skipped", max=self.max_files, count=overflow_count),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
            )

        return len(paths_to_add)

    def add_file(self, path):
        return self.add_files([path], show_limit_warning=True)

    def remove_audio(self, path):
        if self._playing_path == path:
            self._playing_path = None
            self.player.stop()
            self.player.setSource(QUrl())
        if path in self.audio_paths:
            self.audio_paths.remove(path)
        self._durations.pop(path, None)
        self._probe_queue = deque(p for p in self._probe_queue if p != path)
        if not self._probe_queue:
            self._probe_timer.stop()
            self._probing = False
        self._refresh_table()

    def clear_audios(self):
        self._playing_path = None
        self.player.stop()
        self.player.setSource(QUrl())
        self.audio_paths = []
        self._durations.clear()
        self._probe_queue.clear()
        self._probing = False
        self._probe_timer.stop()
        self._refresh_table()

    def stop_playback(self):
        self._playing_path = None
        self.player.stop()

    # --- 表格 ---

    def _refresh_table(self):
        was_playing = self._playing_path
        self._play_buttons.clear()
        self.table.setRowCount(len(self.audio_paths))
        for row, path in enumerate(self.audio_paths):
            name_item = QTableWidgetItem(os.path.basename(path))
            name_item.setToolTip(path)
            self.table.setItem(row, 0, name_item)

            duration_item = QTableWidgetItem(_format_duration(self._durations.get(path)))
            duration_item.setTextAlignment(Qt.AlignCenter)
            duration_item.setToolTip(tr("audio.column.duration"))
            self.table.setItem(row, 1, duration_item)

            self.table.setCellWidget(row, 2, self._make_actions_cell(path))
        self._sync_play_button_icons(self.player.playbackState())
        if was_playing and was_playing not in self.audio_paths:
            self._playing_path = None
        self._update_ui_state()

    def _make_actions_cell(self, path):
        cell = QWidget()
        layout = QHBoxLayout(cell)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(2)

        play_btn = TransparentToolButton(FluentIcon.PLAY)
        play_btn.setFixedSize(26, 26)
        play_btn.setToolTip(tr("audio.tooltip.play"))
        play_btn.clicked.connect(lambda _=False, p=path: self._toggle_play(p))
        self._play_buttons[path] = play_btn

        stop_btn = TransparentToolButton(FluentIcon.CLOSE)
        stop_btn.setFixedSize(26, 26)
        stop_btn.setToolTip(tr("audio.tooltip.stop"))
        stop_btn.clicked.connect(lambda _=False: self.stop_playback())

        remove_btn = TransparentToolButton(FluentIcon.DELETE)
        remove_btn.setFixedSize(26, 26)
        remove_btn.setToolTip(tr("audio.tooltip.delete"))
        remove_btn.clicked.connect(lambda _=False, p=path: self.remove_audio(p))

        layout.addWidget(play_btn)
        layout.addWidget(stop_btn)
        layout.addWidget(remove_btn)
        return cell

    def _update_ui_state(self):
        has_files = bool(self.audio_paths)
        self.add_btn.setVisible(not has_files)
        self.table.setVisible(has_files)

    def _row_for_path(self, path):
        try:
            row = self.audio_paths.index(path)
        except ValueError:
            return -1
        return row

    def _update_duration_cell(self, path):
        row = self._row_for_path(path)
        if row < 0:
            return
        item = self.table.item(row, 1)
        if item is not None:
            item.setText(_format_duration(self._durations.get(path)))

    # --- 播放与时长探测 ---

    def _toggle_play(self, path):
        if self._playing_path == path:
            state = self.player.playbackState()
            if state == QMediaPlayer.PlayingState:
                self.player.pause()
                return
            if state == QMediaPlayer.PausedState:
                self.player.play()
                return

        # 用户手动播放时中止探测队列，避免抢占播放器
        self._probe_queue.clear()
        self._probing = False
        self._playing_path = path
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def _queue_probe(self, path):
        self._probe_queue.append(path)
        self._probe_next()

    def _probe_next(self):
        if not self._probe_queue or self._probing:
            return
        if self._playing_path is not None:
            # 播放中不抢占播放器；停止后会从队列继续
            return
        path = self._probe_queue[0]
        self._probing = True
        self._probe_timer.start(4000)
        self.player.setSource(QUrl.fromLocalFile(path))

    def _on_probe_timeout(self):
        if not self._probing:
            return
        path = self._probe_queue.popleft() if self._probe_queue else None
        print(f"[AudioDropArea] Duration probe timeout: {path}")
        if path is not None:
            self._durations.setdefault(path, 0)
            self._update_duration_cell(path)
        self._probing = False
        QTimer.singleShot(0, self._probe_next)

    def _current_source_path(self):
        source = self.player.source()
        if source.isEmpty():
            return ""
        local = source.toLocalFile()
        if not local:
            return source.toString()
        # QUrl.toLocalFile() 统一返回正斜杠，normpath 归一为 os.path 风格以便与 audio_paths 匹配
        return os.path.normpath(local)

    def _on_duration_changed(self, duration):
        # 切换音源时后端会先发一个 duration=0 的重置事件，只有 >0 才是真实时长
        if duration <= 0:
            return

        path = self._current_source_path()
        if path:
            self._durations[path] = int(duration)
            self._update_duration_cell(path)

        if self._probing and self._probe_queue and self._probe_queue[0] == path:
            self._probe_queue.popleft()
            self._probing = False
            self._probe_timer.stop()
            # 不在播放器自身信号回调里直接 setSource（重入会导致后端崩溃），推迟到事件循环
            QTimer.singleShot(0, self._probe_next)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self._playing_path = None
            # 空闲后继续未完成的时长探测（同样推迟出信号回调）
            self._probing = False
            self._probe_timer.stop()
            QTimer.singleShot(0, self._probe_next)
        self._sync_play_button_icons(state)

    def _sync_play_button_icons(self, state):
        playing = state == QMediaPlayer.PlayingState
        for path, btn in self._play_buttons.items():
            is_current = playing and path == self._playing_path
            btn.setIcon(FluentIcon.PAUSE if is_current else FluentIcon.PLAY)
            btn.setToolTip(tr("audio.tooltip.pause") if is_current else tr("audio.tooltip.play"))

    def _on_player_error(self, _source, error, error_string):
        print(f"[AudioDropArea] Player error {error}: {error_string}")
        if self._probing:
            self._probe_timer.stop()
            path = self._probe_queue.popleft() if self._probe_queue else None
            if path is not None:
                self._durations[path] = 0
                self._update_duration_cell(path)
            self._probing = False
            QTimer.singleShot(0, self._probe_next)

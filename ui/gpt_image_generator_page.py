import os
import base64
from PySide6.QtCore import Qt, Signal, QThread, QUrl, QSize, QRect
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QFrame, QSizePolicy, QToolButton, QScrollArea, QSplitter
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QImage, QIcon, QPainter, QPen, QFont, QMouseEvent, QColor
from qfluentwidgets import (CardWidget, PrimaryPushButton, ComboBox, TextEdit, 
                            ImageLabel, StrongBodyLabel, CaptionLabel, InfoBar, InfoBarPosition, FluentIcon, TransparentToolButton)

from core.config import cfg
from core.api_client import gpt_image_api
from core.history_manager import history_mgr

class ImageThumbnail(QWidget):
    removed = Signal(str)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.setFixedSize(100, 100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.img_label = QLabel()
        self.img_label.setScaledContents(True)
        self.img_label.setStyleSheet("border-radius: 8px; border: 1px solid #ddd;")
        
        pixmap = QPixmap(path)
        if not pixmap.isNull():
             # Crop center or just scale? Scale keeping aspect ratio by expanding then crop is better but complex.
             # Simple scale for now
             self.img_label.setPixmap(pixmap)
        
        layout.addWidget(self.img_label)
        
        # Close button overlay
        self.close_btn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.move(72, 4)
        self.close_btn.clicked.connect(self.on_remove)
        
    def on_remove(self):
        self.removed.emit(self.path)

class ImageDropArea(QFrame):
    imageDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setStyleSheet("QFrame { border: 2px dashed #aaa; border-radius: 10px; background-color: transparent; }")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Container for content
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel("Drag & Drop Images Here\n(Max 13)\nOr Click to Select\n(Ctrl+V to Paste)")
        self.label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.label)
        
        # Scroll Area for thumbnails
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setFixedHeight(120)
        self.scroll_area.hide()
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignLeft)
        self.scroll_layout.setContentsMargins(10, 5, 10, 5)
        self.scroll_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.content_layout.addWidget(self.scroll_area)
        
        self.layout.addWidget(self.content_widget)
        
        # Clear All button (top right)
        self.clear_btn = TransparentToolButton(FluentIcon.DELETE, self)
        self.clear_btn.setFixedSize(30, 30)
        self.clear_btn.setToolTip("Clear All Images")
        self.clear_btn.move(self.width() - 35, 5)
        self.clear_btn.clicked.connect(self.clear_images)
        self.clear_btn.hide()
        
        # Paste button (bottom right)
        self.paste_btn = TransparentToolButton(FluentIcon.PASTE, self)
        self.paste_btn.setFixedSize(30, 30)
        self.paste_btn.setToolTip("Paste from Clipboard")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        
        self.image_paths = []

    def resizeEvent(self, event):
        self.clear_btn.move(self.width() - 35, 5)
        self.paste_btn.move(self.width() - 35, self.height() - 35)
        super().resizeEvent(event)

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                import tempfile
                from datetime import datetime
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"paste_image_{int(datetime.now().timestamp())}.png")
                image.save(temp_path, "PNG")
                self.add_image(temp_path)
                InfoBar.success(title="Pasted", content="Image pasted from clipboard.", parent=self, position=InfoBarPosition.TOP_RIGHT)
                return

        if mime_data.hasUrls():
            for url in mime_data.urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    self.add_image(path)
            InfoBar.success(title="Pasted", content="Image file(s) pasted from clipboard.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        
        InfoBar.warning(title="No Image", content="No image found in clipboard.", parent=self, position=InfoBarPosition.TOP_RIGHT)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    self.add_image(path)
        elif event.mimeData().hasImage():
            # Handle raw image data if needed
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # If clicking on empty space, open dialog
            # But we have thumbnails now, so we need to be careful not to block them?
            # The thumbnails are in scroll_area which is a child.
            # If we click on the frame but not on a child widget...
            # Actually QScrollArea will handle its own clicks.
            
            fnames, _ = QFileDialog.getOpenFileNames(self, 'Open files', '', "Image files (*.jpg *.jpeg *.png *.webp)")
            if fnames:
                for fname in fnames:
                    self.add_image(fname)

    def add_image(self, path):
        if len(self.image_paths) >= 13:
            InfoBar.warning(title="Limit Reached", content="Maximum 13 images allowed.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
            
        if path in self.image_paths:
             return

        self.image_paths.append(path)
        thumb = ImageThumbnail(path)
        thumb.removed.connect(self.remove_image)
        self.scroll_layout.addWidget(thumb)
        self.update_ui_state()
        self.imageDropped.emit(path)

    def remove_image(self, path):
        if path in self.image_paths:
            self.image_paths.remove(path)
            # Find widget and remove
            for i in range(self.scroll_layout.count()):
                item = self.scroll_layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, ImageThumbnail) and widget.path == path:
                    widget.deleteLater()
                    break
            self.update_ui_state()

    def clear_images(self):
        self.image_paths = []
        # Clear widgets
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.update_ui_state()
        self.imageDropped.emit("")

    def update_ui_state(self):
        if self.image_paths:
            self.label.hide()
            self.scroll_area.show()
            self.clear_btn.show()
            self.clear_btn.raise_()
        else:
            self.label.show()
            self.scroll_area.hide()
            self.clear_btn.hide()

class AspectRatioLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd; border-radius: 8px;")
        self._pixmap = None

    def setImage(self, path):
        if path and os.path.exists(path):
            self._pixmap = QPixmap(path)
            self.update_pixmap()
        else:
            self._pixmap = None
            self.clear()

    def resizeEvent(self, event):
        self.update_pixmap()
        super().resizeEvent(event)

    def update_pixmap(self):
        if self._pixmap and not self._pixmap.isNull():
            # Scale pixmap to fit the label size, keeping aspect ratio
            # Use a slightly smaller size to ensure borders are visible
            target_size = self.size() - QSize(4, 4) 
            scaled = self._pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled)

class ModernToggleButton(TransparentToolButton):
    """Modern toggle button for preview panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.is_expanded = True  # True means right panel is visible
        self.update_icon()
    
    def update_icon(self):
        """Update icon based on expanded state"""
        if self.is_expanded:
            self.setIcon(FluentIcon.PAGE_RIGHT)
            self.setToolTip("Collapse Preview")
        else:
            self.setIcon(FluentIcon.PAGE_LEFT)
            self.setToolTip("Expand Preview")
    
    def set_expanded(self, expanded: bool):
        """Set the expanded state and update the icon"""
        self.is_expanded = expanded
        self.update_icon()

class GptImageGeneratorPage(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("GptImageGeneratorPage")
        self._previous_window_width = None  # Store the window width before collapsing
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for left and right panels
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left Side - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        # Image Upload with toggle button
        self.drop_area = ImageDropArea()
        self.drop_area.setFixedHeight(200)
        
        # Header layout for Reference Image label and toggle button
        header_layout = QHBoxLayout()
        header_layout.addWidget(StrongBodyLabel("Reference Image (Optional)"))
        header_layout.addStretch()
        
        # Modern toggle button
        self.toggle_btn = ModernToggleButton()
        self.toggle_btn.clicked.connect(self.toggle_preview)
        header_layout.addWidget(self.toggle_btn)
        
        left_layout.addLayout(header_layout)
        left_layout.addWidget(self.drop_area)

        # Prompt
        left_layout.addWidget(StrongBodyLabel("Prompt"))
        self.prompt_edit = TextEdit()
        self.prompt_edit.setStyleSheet("font-size: 11px;") 
        self.prompt_edit.setPlaceholderText("Enter your prompt here...")
        self.prompt_edit.setFixedHeight(200)
        left_layout.addWidget(self.prompt_edit)

        # Settings
        settings_card = CardWidget()
        settings_layout = QVBoxLayout(settings_card)
        
        # Model
        settings_layout.addWidget(CaptionLabel("Model"))
        self.model_combo = ComboBox()
        self.model_combo.addItems(["sora-image"])
        self.model_combo.setCurrentText(cfg.get("gpt_image_last_model"))
        settings_layout.addWidget(self.model_combo)

        # Size (Aspect Ratio for GPT Image)
        settings_layout.addWidget(CaptionLabel("Size"))
        self.size_combo = ComboBox()
        self.size_combo.addItems(["auto", "1:1", "3:2", "2:3"])
        self.size_combo.setCurrentText(cfg.get("gpt_image_last_size"))
        settings_layout.addWidget(self.size_combo)

        # Variants
        settings_layout.addWidget(CaptionLabel("Variants"))
        self.variants_combo = ComboBox()
        self.variants_combo.addItems(["1", "2"])
        self.variants_combo.setCurrentText(str(cfg.get("gpt_image_last_variants")))
        settings_layout.addWidget(self.variants_combo)

        left_layout.addWidget(settings_card)

        # Generate Button
        self.gen_btn = PrimaryPushButton("Generate Image")
        self.gen_btn.clicked.connect(self.on_generate)
        left_layout.addWidget(self.gen_btn)
        
        # Status label moved to left side below generate button
        self.status_label = CaptionLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        
        # Right Side - Preview
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        
        # Header with title
        header_layout = QHBoxLayout()
        header_layout.addWidget(StrongBodyLabel("Result Image"))
        header_layout.addStretch()
        
        right_layout.addLayout(header_layout)
        
        # Use a container for the image to handle resizing better
        self.image_container = QWidget()
        self.image_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container_layout = QVBoxLayout(self.image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self.image_container.setMinimumWidth(200)
        self.preview_label = AspectRatioLabel()
        self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        container_layout.addWidget(self.preview_label)
        right_layout.addWidget(self.image_container, 1) # Give it stretch factor
        
        # Track preview collapsed state
        self.is_preview_collapsed = False
        
        # Set fixed width for left panel and minimum width for right panel
        left_panel.setFixedWidth(400)  # Fixed width for left panel
        self.right_panel.setMinimumWidth(200)  # Minimum width for right panel
        
        # Add panels to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.right_panel)
        
        # Set stretch factors (left panel doesn't stretch, right panel does)
        self.splitter.setStretchFactor(0, 0)  # Left panel
        self.splitter.setStretchFactor(1, 1)  # Right panel
        
        # Set initial sizes (400 for left, rest for right)
        self.splitter.setSizes([400, 700])
        
        # Disable splitter handle to prevent dragging
        self.splitter.handle(1).setEnabled(False)
        
        # Set minimum size for the entire widget
        self.setMinimumWidth(650)  # navigation(50) + left(400) + right_min(200)
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mime_data()
            if mime_data.hasImage():
                image = clipboard.image()
                if not image.isNull():
                    # Save to a temporary file
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, f"paste_image_{int(datetime.now().timestamp())}.png")
                    image.save(temp_path, "PNG")
                    self.drop_area.add_image(temp_path)
                    InfoBar.success(title="Pasted", content="Image pasted from clipboard.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            elif mime_data.hasUrls():
                # Handle file copy-paste
                for url in mime_data.urls():
                    path = url.toLocalFile()
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        self.drop_area.add_image(path)
                        break

    def on_generate(self):
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            InfoBar.warning(title="Warning", content="Please enter a prompt.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return

        model = self.model_combo.currentText()
        size = self.size_combo.currentText()
        variants = int(self.variants_combo.currentText())
        
        # Save settings
        cfg.set("gpt_image_last_model", model)
        cfg.set("gpt_image_last_size", size)
        cfg.set("gpt_image_last_variants", variants)

        # Handle Images
        ref_urls = []
        # self.drop_area.image_paths is a list now
        for img_path in self.drop_area.image_paths:
            try:
                with open(img_path, "rb") as img_file:
                    b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                    # Guess mime type
                    ext = os.path.splitext(img_path)[1].lower().replace('.', '')
                    if ext == 'jpg': ext = 'jpeg'
                    data_uri = f"data:image/{ext};base64,{b64_string}"
                    ref_urls.append(data_uri)
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")

        # Submit Task
        self.gen_btn.setEnabled(False)
        self.status_label.setText("Submitting task...")
        
        # Run in background to avoid freezing UI
        self.submit_thread = GptSubmitTaskThread(prompt, model, size, variants, ref_urls)
        self.submit_thread.finished.connect(self.on_submit_finished)
        self.submit_thread.start()
        
        # Keep track of background threads
        if not hasattr(self, 'background_threads'):
            self.background_threads = []

    def on_submit_finished(self, result):
        self.gen_btn.setEnabled(True)
        if result.get("code") == 0:
            task_id = result["data"]["id"]
            InfoBar.success(title="Success", content="Task submitted successfully.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            self.status_label.setText(f"Task ID: {task_id} - Waiting for results...")
            
            # Add to history
            # Pass the list of paths
            history_mgr.add_gpt_task(
                task_id, 
                self.prompt_edit.toPlainText(), 
                self.model_combo.currentText(),
                self.size_combo.currentText(),
                self.variants_combo.currentText(),
                self.drop_area.image_paths
            )
            
            # If there was a previous polling thread active on the UI, disconnect it from UI updates
            if hasattr(self, 'current_poll_thread') and self.current_poll_thread.isRunning():
                try:
                    self.current_poll_thread.update_signal.disconnect(self.on_poll_update)
                    self.current_poll_thread.finished_signal.disconnect(self.on_poll_finished)
                except:
                    pass
            
            # Start polling for this specific task
            self.current_poll_thread = GptPollTaskThread(task_id)
            self.current_poll_thread.update_signal.connect(self.on_poll_update)
            self.current_poll_thread.finished_signal.connect(self.on_poll_finished)
            
            # Add to background threads to keep reference
            self.background_threads.append(self.current_poll_thread)
            
            # Clean up finished threads from list
            self.current_poll_thread.finished.connect(lambda: self.cleanup_thread(self.current_poll_thread))
            
            self.current_poll_thread.start()
            
        else:
            InfoBar.error(title="Error", content=f"Submission failed: {result.get('msg')}", parent=self, position=InfoBarPosition.TOP_RIGHT)
            self.status_label.setText("Submission failed.")

    def cleanup_thread(self, thread):
        if thread in self.background_threads:
            self.background_threads.remove(thread)

    def on_poll_update(self, progress, status):
        self.status_label.setText(f"Status: {status} - Progress: {progress}%")

    def toggle_preview(self):
        """Toggle the collapsed state of the entire right panel"""
        self.is_preview_collapsed = not self.is_preview_collapsed
        
        if self.is_preview_collapsed:
            # Collapse: hide entire right panel and update toggle button
            self.right_panel.hide()
            self.toggle_btn.set_expanded(False)
            
            # Store current window width before collapsing
            if self.parent_window:
                self._previous_window_width = self.parent_window.width()
                # Adjust window width to fit only left panel + navigation
                self.parent_window.resize(450, self.parent_window.height())  # Left panel (400) + Navigation (50)
        else:
            # Expand: show entire right panel and update toggle button
            self.right_panel.show()
            self.toggle_btn.set_expanded(True)
            
            # Restore window width to previously stored value or default
            if self.parent_window:
                if self._previous_window_width and self._previous_window_width > 450:
                    # Restore to the previously stored width
                    self.parent_window.resize(self._previous_window_width, self.parent_window.height())
                else:
                    # Use default width if no previous width stored or it's too small
                    self.parent_window.resize(1100, self.parent_window.height())
            
            # If there's a current image that was hidden, refresh it
            if hasattr(self, '_last_generated_image') and self._last_generated_image:
                self.preview_label.setImage(self._last_generated_image)

    def on_poll_finished(self, task_id, success, result_path, msg):
        if success:
            self.status_label.setText("Generation Complete!")
            # Save the last generated image path for later use
            self._last_generated_image = result_path
            # Only set the image if preview is not collapsed
            if not self.is_preview_collapsed:
                self.preview_label.setImage(result_path)
            InfoBar.success(title="Done", content="Image generated successfully.", parent=self, position=InfoBarPosition.TOP_RIGHT)
        else:
            self.status_label.setText(f"Failed: {msg}")
            InfoBar.error(title="Failed", content=msg, parent=self, position=InfoBarPosition.TOP_RIGHT)

class GptSubmitTaskThread(QThread):
    finished = Signal(dict)

    def __init__(self, prompt, model, size, variants, ref_urls):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.size = size
        self.variants = variants
        self.ref_urls = ref_urls

    def run(self):
        res = gpt_image_api.submit_task(self.prompt, self.model, self.size, self.variants, self.ref_urls)
        self.finished.emit(res)

class GptPollTaskThread(QThread):
    update_signal = Signal(int, str)
    finished_signal = Signal(str, bool, str, str)

    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id

    def run(self):
        import time
        import requests
        
        error_count = 0
        while True:
            try:
                res = gpt_image_api.get_task_result(self.task_id)
                error_count = 0 # Reset on success
            except Exception as e:
                error_count += 1
                if error_count > 5:
                    self.finished_signal.emit(self.task_id, False, "", f"Network error: {str(e)}")
                    return
                time.sleep(2)
                continue

            if res.get("code") != 0:
                # If task not found or other API error, maybe wait a bit or fail
                if res.get("code") == -22: # Task not found, maybe not ready yet?
                    time.sleep(2)
                    continue
                self.finished_signal.emit(self.task_id, False, "", res.get("msg", "Unknown error"))
                return

            data = res.get("data", {})
            status = data.get("status")
            progress = data.get("progress", 0)
            
            self.update_signal.emit(progress, status)

            if status == "succeeded":
                results = data.get("results", [])
                if results:
                    # Download all images for multi-variant support
                    downloaded_files = []
                    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                    
                    for i, result in enumerate(results):
                        img_url = result.get("url")
                        if not img_url:
                            continue
                            
                        try:
                            img_data = requests.get(img_url).content
                            ext = "png" # Default
                            if ".jpg" in img_url: ext = "jpg"
                            if ".jpeg" in img_url: ext = "jpeg"
                            
                            # Add suffix for multiple images
                            if len(results) > 1:
                                filename = f"grsai_{timestamp}_{i+1}.{ext}"
                            else:
                                filename = f"grsai_{timestamp}.{ext}"
                                
                            output_dir = cfg.get("output_folder")
                            if not os.path.exists(output_dir):
                                os.makedirs(output_dir)
                                
                            filepath = os.path.join(output_dir, filename)
                            with open(filepath, "wb") as f:
                                f.write(img_data)
                                
                            downloaded_files.append(filepath)
                        except Exception as e:
                            print(f"Error downloading image {i+1}: {e}")
                    
                    if downloaded_files:
                        # Use first image for preview, but store all paths
                        preview_url = results[0].get("url")
                        history_mgr.update_gpt_task(self.task_id, "succeeded", result_path=downloaded_files[0], preview_url=preview_url)
                        self.finished_signal.emit(self.task_id, True, downloaded_files[0], "Success")
                    else:
                        history_mgr.update_gpt_task(self.task_id, "failed", failure_reason="Failed to download any images")
                        self.finished_signal.emit(self.task_id, False, "", "Failed to download any images")
                else:
                    history_mgr.update_gpt_task(self.task_id, "failed", failure_reason="No results found")
                    self.finished_signal.emit(self.task_id, False, "", "No results found")
                return

            elif status == "failed":
                reason = data.get("failure_reason", "Unknown")
                history_mgr.update_gpt_task(self.task_id, "failed", failure_reason=reason)
                self.finished_signal.emit(self.task_id, False, "", reason)
                return

            time.sleep(2)

from PySide6.QtWidgets import QApplication
from datetime import datetime

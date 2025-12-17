from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon, SplashScreen

from ui.banana_generator_page import BananaGeneratorPage
from ui.gpt_image_generator_page import GptImageGeneratorPage
from ui.history_page import HistoryPage
from ui.settings_page import SettingsPage

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()

        # Create sub interfaces
        self.banana_generator_interface = BananaGeneratorPage(self)
        self.gpt_generator_interface = GptImageGeneratorPage(self)
        self.history_interface = HistoryPage()
        self.settings_interface = SettingsPage()

        self.initNavigation()
        # Set initial window title based on default interface
        self.update_window_title(self.banana_generator_interface)
        # self.splashScreen.finish()

    def initWindow(self):
        self.resize(1100, 750)
        self.setMinimumWidth(450)  # Left panel (400) + Navigation (50)
        self.setWindowTitle('Grsai GUI')
        
        # Center on screen
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def initNavigation(self):
        self.addSubInterface(self.banana_generator_interface, FluentIcon.PHOTO, 'Nano Banana')
        self.addSubInterface(self.gpt_generator_interface, FluentIcon.PHOTO, 'GPT Image')
        #self.addSubInterface(self.sora_generator_interface, FluentIcon.VIDEO, 'Sora')
        #self.addSubInterface(self.veo_generator_interface, FluentIcon.VIDEO, 'Veo')
        self.addSubInterface(self.history_interface, FluentIcon.HISTORY, 'History')
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, 'Settings', position=NavigationItemPosition.BOTTOM)

    def switchTo(self, interface):
        """Override switchTo to update window title when switching interfaces"""
        super().switchTo(interface)
        self.update_window_title(interface)

    def update_window_title(self, interface):
        """Update window title based on current interface"""
        base_title = 'Grsai GUI'
        
        if interface == self.banana_generator_interface:
            self.setWindowTitle(f'{base_title} - Nano Banana')
        elif interface == self.gpt_generator_interface:
            self.setWindowTitle(f'{base_title} - GPT Image')
        elif interface == self.history_interface:
            self.setWindowTitle(f'{base_title} - History')
        elif interface == self.settings_interface:
            self.setWindowTitle(f'{base_title} - Settings')
        else:
            self.setWindowTitle(base_title)

    def regenerate_task(self, task_data):
        # Determine which interface to use based on API type
        api_type = task_data.get('api_type', 'nano_banana')
        
        if api_type == 'gpt_image':
            # Switch to GPT Image generator page
            self.switchTo(self.gpt_generator_interface)
            
            # Populate fields
            self.gpt_generator_interface.prompt_edit.setText(task_data['prompt'])
            self.gpt_generator_interface.model_combo.setCurrentText(task_data['model'])
            self.gpt_generator_interface.size_combo.setCurrentText(task_data['size'])
            self.gpt_generator_interface.variants_combo.setCurrentText(str(task_data['variants']))
            
            # Handle reference image if it exists
            # Clear existing images first
            self.gpt_generator_interface.drop_area.clear_images()
            
            if task_data.get('ref_images'):
                ref_imgs = task_data['ref_images']
                if isinstance(ref_imgs, str):
                    self.gpt_generator_interface.drop_area.add_image(ref_imgs)
                elif isinstance(ref_imgs, list):
                    for img_path in ref_imgs:
                        self.gpt_generator_interface.drop_area.add_image(img_path)
        else:
            # Switch to Nano Banana generator page
            self.switchTo(self.banana_generator_interface)
            
            # Populate fields
            self.banana_generator_interface.prompt_edit.setText(task_data['prompt'])
            self.banana_generator_interface.model_combo.setCurrentText(task_data['model'])
            self.banana_generator_interface.ratio_combo.setCurrentText(task_data['aspect_ratio'])
            self.banana_generator_interface.size_combo.setCurrentText(task_data['image_size'])
            
            # Handle reference image if it exists
            # Clear existing images first
            self.banana_generator_interface.drop_area.clear_images()
            
            if task_data.get('ref_images'):
                ref_imgs = task_data['ref_images']
                if isinstance(ref_imgs, str):
                    self.banana_generator_interface.drop_area.add_image(ref_imgs)
                elif isinstance(ref_imgs, list):
                    for img_path in ref_imgs:
                        self.banana_generator_interface.drop_area.add_image(img_path)
        
        # Do not trigger generation automatically, let user decide
        # self.generator_interface.on_generate()

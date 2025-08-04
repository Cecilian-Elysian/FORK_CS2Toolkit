from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QApplication


class AnimationManager:
    def __init__(self, parent):
        self.parent = parent
        self.button_animation = None
        self.button_release_animation = None
        self.text_timer = None
        self.text_index = 0
        self.target_text = ""
        self.current_line_edit = None
    
    def animate_button_click(self, button):
        self.button_animation = QPropertyAnimation(button, b"geometry")
        self.button_animation.setDuration(100)
        original_rect = button.geometry()
        smaller_rect = original_rect.adjusted(2, 2, -2, -2)
        
        self.button_animation.setStartValue(original_rect)
        self.button_animation.setEndValue(smaller_rect)
        self.button_animation.setEasingCurve(QEasingCurve.OutQuad)
        
        self.button_animation.finished.connect(lambda: self.animate_button_release(button, original_rect))
        self.button_animation.start()
    
    def animate_button_release(self, button, original_rect):
        self.button_release_animation = QPropertyAnimation(button, b"geometry")
        self.button_release_animation.setDuration(100)
        self.button_release_animation.setStartValue(button.geometry())
        self.button_release_animation.setEndValue(original_rect)
        self.button_release_animation.setEasingCurve(QEasingCurve.OutBounce)
        self.button_release_animation.start()
    
    def animate_text_input(self, line_edit, text):
        line_edit.clear()
        self.text_timer = QTimer()
        self.text_index = 0
        self.target_text = text
        self.current_line_edit = line_edit
        
        def add_char():
            if self.text_index < len(self.target_text):
                current_text = self.target_text[:self.text_index + 1]
                self.current_line_edit.setText(current_text)
                self.text_index += 1
            else:
                self.text_timer.stop()
        
        self.text_timer.timeout.connect(add_char)
        self.text_timer.start(20)
    
    def show_loading_animation(self, steam_entry, font_steam_entry):
        if steam_entry:
            steam_entry.setPlaceholderText("正在检测Steam路径...")
        if font_steam_entry:
            font_steam_entry.setPlaceholderText("正在检测Steam路径...")
    
    def hide_loading_animation(self, steam_entry, font_steam_entry):
        if steam_entry:
            steam_entry.setPlaceholderText("自动检测或手动选择...")
        if font_steam_entry:
            font_steam_entry.setPlaceholderText("自动检测或手动选择...")
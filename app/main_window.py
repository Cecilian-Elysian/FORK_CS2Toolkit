import os
import json
import threading
from PySide6.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QInputDialog
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QImage, QIcon, QDesktopServices
from PySide6.QtCore import QUrl
from qfluentwidgets import (setTheme, Theme, InfoBar, FluentWindow, NavigationItemPosition,
                           MessageBox)
from app.logic.config_manager import ConfigManager
from app.logic.font_replacer import FontReplacer
from app.logic.video_replacer import VideoReplacer
from app.logic.steam_utils import SteamUtils, PathValidator
from app.logic.sound_replacer import SoundReplacer
from app.logic.gsi_manager import GSIManager
from app.ui.animations import AnimationManager
from app.ui.pages.home_page import HomePage
from app.ui.integrated_sound_page import IntegratedSoundPage
from app.ui.components import VideoPresetWidget, FontPresetWidget, SoundPresetWidget
from app.assets import (app_icon, font_icon, home_icon, video_icon, info_icon,
                        sun_icon, moon_icon, sound_icon, home_blue, sound_blue,
                        video_blue, font_blue, info_blue, listener, listener_blue)

# Qt 资源文件：提供所有 :/xxx.ico 图标路径
import app.assets.video_resources  # noqa: F401

class GsiSignalEmitter(QObject):
    data_received = Signal(dict)

class UpdateSignalEmitter(QObject):
    update_found = Signal(dict)

class CS2Tool(FluentWindow):
    def __init__(self):
        super().__init__()
        self.version = "1.2.2"
        self.is_dark_mode = False
        self.config_manager = ConfigManager()
        self.animation_manager = AnimationManager(self)
        self.gsi_manager = GSIManager(config_manager=self.config_manager)
        self.steam_path = "" 
        self.video_path = ""
        self.font_path = ""
        self.sound_path = ""

        self.gsi_signal_emitter = GsiSignalEmitter()
        self.gsi_signal_emitter.data_received.connect(self.handle_gsi_data_on_ui_thread)
        self.gsi_manager.register_data_callback(self.handle_gsi_data_from_thread)

        self.update_signal_emitter = UpdateSignalEmitter()
        self.update_signal_emitter.update_found.connect(self.show_update_dialog)
        
        self.init_window()
        self.init_ui()

        self.load_all_presets()
        self.update_home_status()
        # 延迟执行：让窗口先显示，500ms 后再检测 Steam 和检查更新
        QTimer.singleShot(500, self._deferred_startup_tasks)

    def _deferred_startup_tasks(self):
        self.auto_detect_steam()
        self.check_for_updates()

    def init_window(self):
        self.setWindowTitle("CS2 工具箱")
        self.setWindowIcon(QIcon(":/app_icon.ico"))
        self.resize(620, 780)
        self.center()

        from PySide6.QtWidgets import QPushButton, QWidget
        from PySide6.QtCore import QSize
        self.theme_button = QPushButton()
        self.theme_button.setIcon(QIcon(":/moon.ico"))
        self.theme_button.setFixedSize(38, 30)
        self.theme_button.setIconSize(QSize(18, 18))
        self.theme_button.clicked.connect(self.toggle_theme)
        
        button_container = QWidget()
        button_container.setFixedSize(50, 30)
        from PySide6.QtWidgets import QHBoxLayout
        container_layout = QHBoxLayout(button_container)
        container_layout.setContentsMargins(12, 0, 0, 0)
        container_layout.addWidget(self.theme_button)
        
        self.update_theme_button_style()
        
        self.titleBar.hBoxLayout.insertWidget(
            self.titleBar.hBoxLayout.count() - 1,
            button_container,
            0,
            Qt.AlignVCenter
        )

    def init_ui(self):
        from app.ui.pages.video_page import VideoPage
        from app.ui.pages.font_page import FontPage
        from app.ui.pages.about_page import AboutPage
        from app.ui.pages.sound_page import SoundPage

        self.home_tab = HomePage(self)
        self.home_tab.setObjectName("home_tab")

        self.video_tab = VideoPage(self)
        self.video_tab.setObjectName("video_tab")

        self.font_tab = FontPage(self)
        self.font_tab.setObjectName("font_tab")

        self.about_tab = AboutPage(self)
        self.about_tab.setObjectName("about_tab")

        self.sound_tab = SoundPage(self)
        self.sound_tab.setObjectName("sound_tab")

        self.integrated_sound_page = IntegratedSoundPage(self.gsi_manager, self.config_manager, self)
        self.integrated_sound_page.setObjectName("integrated_sound_page")
        
        self.gsi_tab = self.integrated_sound_page
        self.gsi_page = self.integrated_sound_page  
        self.gsi_sound_page = self.integrated_sound_page  
        

        
        self.addSubInterface(self.home_tab, QIcon(":/home_blue.ico"), "主页", NavigationItemPosition.TOP)
        self.addSubInterface(self.video_tab, QIcon(":/video_blue.ico"), "开屏替换")
        self.addSubInterface(self.sound_tab, QIcon(":/sound_blue.ico"), "启动音效替换")
        self.addSubInterface(self.integrated_sound_page, QIcon(":/listener_blue.ico"), "GSI实时音效")
        self.addSubInterface(self.font_tab, QIcon(":/font_blue.ico"), "字体替换")
        self.addSubInterface(self.about_tab, QIcon(":/info_blue.ico"), "关于", NavigationItemPosition.BOTTOM)

        setTheme(Theme.LIGHT)

    def load_all_presets(self):
        self.load_video_presets()
        self.load_font_presets()
        self.load_sound_presets()

    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_navigation_icons(self):
        if self.is_dark_mode:
            self.navigationInterface.widget(self.home_tab.objectName()).setIcon(QIcon(":/home.ico"))
            self.navigationInterface.widget(self.video_tab.objectName()).setIcon(QIcon(":/video.ico"))
            self.navigationInterface.widget(self.sound_tab.objectName()).setIcon(QIcon(":/sound.ico"))
            self.navigationInterface.widget(self.gsi_tab.objectName()).setIcon(QIcon(":/listener.ico"))
            self.navigationInterface.widget(self.font_tab.objectName()).setIcon(QIcon(":/font.ico"))
            self.navigationInterface.widget(self.about_tab.objectName()).setIcon(QIcon(":/info.ico"))
        else:
            self.navigationInterface.widget(self.home_tab.objectName()).setIcon(QIcon(":/home_blue.ico"))
            self.navigationInterface.widget(self.video_tab.objectName()).setIcon(QIcon(":/video_blue.ico"))
            self.navigationInterface.widget(self.sound_tab.objectName()).setIcon(QIcon(":/sound_blue.ico"))
            self.navigationInterface.widget(self.gsi_tab.objectName()).setIcon(QIcon(":/listener_blue.ico"))
            self.navigationInterface.widget(self.font_tab.objectName()).setIcon(QIcon(":/font_blue.ico"))
            self.navigationInterface.widget(self.about_tab.objectName()).setIcon(QIcon(":/info_blue.ico"))

    def update_theme_button_style(self):
        if self.is_dark_mode:
            style = """
                QPushButton {
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    background: rgba(255, 255, 255, 0.05);
                    padding: 0px;
                    qproperty-iconSize: 18px 18px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.5);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.25);
                }
            """
        else:
            style = """
                QPushButton {
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    border-radius: 4px;
                    background: rgba(0, 0, 0, 0.05);
                    padding: 0px;
                    qproperty-iconSize: 18px 18px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(0, 0, 0, 0.3);
                }
                QPushButton:pressed {
                    background-color: rgba(0, 0, 0, 0.15);
                }
            """
        self.theme_button.setStyleSheet(style)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        
        if self.is_dark_mode:
            setTheme(Theme.DARK)
            self.theme_button.setIcon(QIcon(":/sun.ico"))
        else:
            setTheme(Theme.LIGHT)
            self.theme_button.setIcon(QIcon(":/moon.ico"))
        
        self.update_theme_button_style()
        self.update_navigation_icons()
        
    
    def quick_detect_steam(self):
        """Detects CS2 path and updates UI."""
        self.auto_detect_steam()

    def update_recent_activity(self, activity):
        self.home_tab.recent_activity_label.setText(f"最近: {activity}")

    def update_home_status(self):
        if hasattr(self, 'home_tab'):
            if self.steam_path and os.path.exists(self.steam_path):
                self.home_tab.steam_status_label.setText(f"CS2路径: {self.steam_path}")
            else:
                self.home_tab.steam_status_label.setText("CS2路径: 未设置")
            
            self.home_tab.video_count_label.setText(f"视频预设: {len(self.config_manager.get_presets('video'))} 个")
            self.home_tab.sound_count_label.setText(f"音效预设: {len(self.config_manager.get_presets('sound'))} 个")
            self.home_tab.font_count_label.setText(f"字体预设: {len(self.config_manager.get_presets('font'))} 个")

    def browse_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", "WebM 视频 (*.webm)")
        if path:
            self.video_tab.video_entry.setText(path)

    def load_video_presets(self):
        self.video_tab.preset_list.clear()
        for i, preset in enumerate(self.config_manager.get_presets('video')):
            item = QListWidgetItem(self.video_tab.preset_list)
            widget = VideoPresetWidget(preset, self.apply_preset)
            item.setSizeHint(widget.sizeHint())
            self.video_tab.preset_list.setItemWidget(item, widget)

    def open_preset_folder(self, path):
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            self.show_error("路径不存在", f"文件夹 '{folder}' 不存在。")

    def _request_thumbnail(self, video_path, on_done):
        """使用 QtMultimedia 异步截取视频第一帧作为缩略图（替代 cv2）"""
        import uuid
        from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
        from PySide6.QtCore import QUrl

        player = QMediaPlayer(self)
        sink = QVideoSink(self)
        player.setVideoSink(sink)
        done = []

        def _on_frame_changed(frame):
            if done:
                return
            if not frame.isValid():
                return
            img = frame.toImage()
            if img.isNull():
                return
            done.append(True)
            try:
                path = os.path.join(
                    self.config_manager.get_thumbnail_dir(),
                    f"{uuid.uuid4().hex}.png",
                )
                img.save(path)
                on_done(path)
            except Exception as e:
                print(f"缩略图保存失败: {e}")
                on_done(None)
            finally:
                player.stop()
                player.deleteLater()
                sink.deleteLater()

        sink.videoFrameChanged.connect(_on_frame_changed)
        player.setSource(QUrl.fromLocalFile(video_path))
        player.play()
        # 兜底：2秒后如果没截到帧则放弃
        QTimer.singleShot(2000, lambda: (
            player.stop(), player.deleteLater(), sink.deleteLater(), on_done(None)
        ) if not done else None)

    def save_preset(self):
        video_path = self.video_tab.video_entry.text()
        if not video_path:
            self.show_warning("操作无效", "请先选择一个视频文件。")
            return

        name, ok = self.get_input_dialog("保存预设", "输入预设名称:", f"预设 {len(self.config_manager.get_presets('video')) + 1}")
        if not ok or not name:
            return

        def _on_thumbnail_ready(thumbnail_path):
            if not thumbnail_path:
                self.show_error("保存失败", "无法生成视频缩略图。")
                return
            self.config_manager.add_preset('video', name=name, video_path=video_path, thumbnail_path=thumbnail_path)
            self.load_video_presets()
            self.update_home_status()
            self.update_recent_activity(f"保存视频预设: {name}")
            self.show_success("成功", "视频预设已保存。")

        self._request_thumbnail(video_path, _on_thumbnail_ready)

    def delete_preset_confirm(self, index):
        title = "确认删除"
        video_presets = self.config_manager.get_presets('video')
        content = f"确定要删除预设 '{video_presets[index]['name']}' 吗？"
        if self.show_confirm_dialog(title, content):
            preset_name = video_presets[index]['name']
            self.config_manager.delete_preset('video', index)
            self.load_video_presets()
            self.update_home_status()
            self.update_recent_activity(f"删除视频预设: {preset_name}")

    def apply_preset(self, preset):
        if not os.path.exists(preset["video_path"]):
            self.show_error("文件丢失", "预设的视频文件已不存在。")
            return
        
        self.video_tab.video_entry.setText(preset["video_path"])
        
        if self.show_confirm_dialog("确认应用", f"是否立即应用视频预设 '{preset['name']}'？"):
            self.execute_replace()

    def apply_preset_from_item(self, item):
        index = self.video_tab.preset_list.row(item)
        video_presets = self.config_manager.get_presets('video')
        if 0 <= index < len(video_presets):
            self.apply_preset(video_presets[index])

    def auto_detect_steam(self):

        QTimer.singleShot(10, self._perform_steam_detection)

    def _perform_steam_detection(self):
        cs2_path = SteamUtils.find_cs2_install_path()
        if cs2_path and os.path.exists(cs2_path):
            self.steam_path = cs2_path
            self.update_home_status()
            self.update_recent_activity("自动检测CS2路径成功")
            InfoBar.success("成功", "已自动检测到CS2安装路径。", parent=self, duration=3000)
        else:
            self.steam_path = ""
            self.update_home_status()
            InfoBar.warning("提示", "未检测到CS2，请手动选择CS2安装目录。", parent=self, duration=5000)

    def browse_steam(self):
        path = QFileDialog.getExistingDirectory(self, "选择CS2安装目录")
        if path:
            # Basic validation: check for cs2.exe
            if os.path.exists(os.path.join(path, "game", "bin", "win64", "cs2.exe")):
                self.steam_path = path
                self.update_home_status()
                self.update_recent_activity(f"手动设置CS2路径为: {path}")
            else:
                self.show_error("路径无效", "所选目录不是有效的CS2安装目录。")

    def execute_replace(self):
        cs2_path = self.steam_path
        video_path = self.video_tab.video_entry.text()

        if not cs2_path or not os.path.exists(cs2_path):
            self.show_error("路径无效", "CS2路径未设置或无效，请先在主页设置。")
            return
        is_valid, msg = PathValidator.validate_video_file(video_path)
        if not is_valid:
            self.show_error("文件无效", msg)
            return

        self.animation_manager.animate_button_click(self.video_tab.execute_btn)

        version_type = "both"
        if self.video_tab.intl_radio.isChecked(): version_type = "intl"
        if self.video_tab.cn_radio.isChecked(): version_type = "cn"
        
        try:
            steam_library_path = SteamUtils.extract_steam_library_from_cs2_path(cs2_path)
            if not steam_library_path:
                self.show_error("路径转换失败", "无法从CS2路径获取Steam库路径。")
                return
            replacer = VideoReplacer(steam_library_path)
            result = replacer.replace_video(video_path, version_type)
            if result["success"]:
                self.update_recent_activity(f"替换开屏动画成功 ({result['replaced_count']}个文件)")
                self.show_success("替换成功", f"开屏动画已成功替换！共处理 {result['replaced_count']} 个文件。")
            else:
                self.show_error("替换失败", result['error'])
        except Exception as e:
            self.show_error("严重错误", str(e))
    
    def handle_gsi_data_from_thread(self, data_bytes):
        """Receives data from GSI thread and emits a signal to the main thread."""
        try:
            # 尝试多种编码方式解码数据
            data_str = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    data_str = data_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if data_str is None:
                # 如果所有编码都失败，使用错误处理方式
                data_str = data_bytes.decode('utf-8', errors='ignore')
            
            game_state = json.loads(data_str)
            self.gsi_signal_emitter.data_received.emit(game_state)
        except (json.JSONDecodeError, Exception):
            pass # Ignore malformed data

    def handle_gsi_data_on_ui_thread(self, game_state):
        """Handles GSI data on the main UI thread."""
        # 处理服务器启动失败
        if "error" in game_state and game_state["error"] == "server_start_failed":
             self.integrated_sound_page.gsi_status_label.setText(f"错误: {game_state.get('message', '无法启动服务器')}")
             self.integrated_sound_page.gsi_switch.setChecked(False)
             self.show_error("GSI服务启动失败", game_state.get('message', '无法启动服务器'))
             return
        
        # 处理服务器启动成功
        if "success" in game_state and game_state["success"] == "server_started":
            port = game_state.get("port", "未知")
            host = game_state.get("host", "127.0.0.1")
            self.integrated_sound_page.gsi_status_label.setText(f"服务运行中，正在监听CS2... (端口: {port})")
            self.show_success("GSI服务启动成功", f"服务已在 {host}:{port} 端口上开启")
            return
        
        # 处理其他错误
        if "error" in game_state:
            error_type = game_state["error"]
            if error_type == "server_unexpected_error":
                self.integrated_sound_page.gsi_status_label.setText("错误: 服务器发生意外错误")
                self.integrated_sound_page.gsi_switch.setChecked(False)
                self.show_error("GSI服务错误", game_state.get('message', '服务器发生意外错误'))
            return
        
        # 处理正常的游戏状态数据
        if not any(key in game_state for key in ["error", "success"]):
            self.integrated_sound_page.gsi_status_label.setText("服务运行中，正在监听CS2...")
            # This is where the event matching logic will go
            self.integrated_sound_page.process_game_state(game_state)


    def browse_font_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择字体文件", "", "TrueType 字体 (*.ttf)")
        if path:
            is_valid, msg = PathValidator.validate_font_file(path)
            if is_valid:
                self.font_tab.font_entry.setText(path)
                self.font_path = path
                self.update_font_info(path)
            else:
                self.show_error("字体无效", msg)

    def update_font_info(self, font_path):
        if font_path and os.path.exists(font_path):
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            filename = os.path.basename(font_path)
            self.font_tab.font_name_label.setText(f"字体名称: {font_name}")
            self.font_tab.font_filename_label.setText(f"文件名: {filename}")
            pass  # 状态标签已删除
        else:
            self.font_tab.font_name_label.setText("字体名称: 未选择")
            self.font_tab.font_filename_label.setText("文件名: 未选择")
            pass  # 状态标签已删除

    def load_font_presets(self):
        self.font_tab.font_preset_list.clear()
        font_presets = self.config_manager.get_presets('font')
        for i, preset in enumerate(font_presets):
            item = QListWidgetItem(self.font_tab.font_preset_list)
            widget = FontPresetWidget(preset, self.apply_font_preset)
            item.setSizeHint(widget.sizeHint())
            self.font_tab.font_preset_list.setItemWidget(item, widget)

    def save_font_preset(self):
        font_path = self.font_tab.font_entry.text()
        if not font_path or not os.path.exists(font_path):
            self.show_warning("操作无效", "请先选择一个有效的字体文件。")
            return

        name, ok = self.get_input_dialog("保存字体预设", "输入预设名称:")
        if not ok or not name:
            return

        font_presets = self.config_manager.get_presets('font')
        if any(p['name'] == name for p in font_presets):
            self.show_warning("名称重复", "该预设名称已存在。")
            return

        try:
            font_filename = os.path.basename(font_path)
            font_name_extracted = os.path.splitext(font_filename)[0]
            self.config_manager.add_preset('font', name=name, font_path=font_path, font_name=font_name_extracted, font_filename=font_filename)
            self.load_font_presets()
            self.update_home_status()
            self.update_recent_activity(f"保存字体预设: {name}")
            self.show_success("成功", "字体预设已保存。")
        except Exception as e:
            self.show_error("保存失败", str(e))

    def delete_font_preset_confirm(self, index):
        title = "确认删除"
        font_presets = self.config_manager.get_presets('font')
        content = f"确定要删除字体预设 '{font_presets[index]['name']}' 吗？"
        if self.show_confirm_dialog(title, content):
            preset_name = font_presets[index]['name']
            self.config_manager.delete_preset('font', index)
            self.load_font_presets()
            self.update_home_status()
            self.update_recent_activity(f"删除字体预设: {preset_name}")

    def apply_font_preset(self, preset):
        if not os.path.exists(preset["font_path"]):
            self.show_error("文件丢失", "预设的字体文件已不存在。")
            return

        self.font_tab.font_entry.setText(preset["font_path"])
        self.font_path = preset["font_path"]
        self.update_font_info(preset["font_path"])

        if self.show_confirm_dialog("确认应用", f"是否立即应用字体预设 '{preset['name']}'？"):
            self.execute_font_replace()

    def apply_font_preset_from_item(self, item):
        index = self.font_tab.font_preset_list.row(item)
        font_presets = self.config_manager.get_presets('font')
        if 0 <= index < len(font_presets):
            self.apply_font_preset(font_presets[index])

    def execute_font_replace(self):
        if not self.font_path or not os.path.exists(self.font_path):
            self.show_error("文件无效", "请先选择有效的字体文件。")
            return
        cs2_path = self.steam_path
        if not cs2_path or not os.path.exists(cs2_path):
            self.show_error("路径缺失", "CS2路径未设置或无效，请先在主页设置。")
            return

        self.animation_manager.animate_button_click(self.font_tab.execute_font_btn)

        try:
            steam_library_path = SteamUtils.extract_steam_library_from_cs2_path(cs2_path)
            if not steam_library_path:
                self.show_error("路径转换失败", "无法从CS2路径获取Steam库路径。")
                return
            replacer = FontReplacer(steam_library_path)
            QApplication.processEvents()

            result = replacer.replace_font(self.font_path, lambda msg: None)

            if result["success"]:
                self.update_recent_activity(f"替换字体: {result['font_name']}")
                self.show_success("替换成功", f"字体已成功替换为 {result['font_name']}。")
            else:
                self.show_error("替换失败", result['error'])
        except Exception as e:
            self.show_error("严重错误", str(e))
        finally:
            pass  # 状态标签已删除

    def show_info(self, title, content, duration=3000):
        InfoBar.info(title, content, parent=self, duration=duration)

    def show_success(self, title, content, duration=3000):
        InfoBar.success(title, content, parent=self, duration=duration)

    def show_warning(self, title, content, duration=5000):
        InfoBar.warning(title, content, parent=self, duration=duration)

    def show_error(self, title, content, duration=5000):
        InfoBar.error(title, content, parent=self, duration=duration)

    def show_confirm_dialog(self, title, content):
        dialog = MessageBox(title, content, self)
        return dialog.exec()

    def get_input_dialog(self, title, content, default_text=""):
        text, ok = QInputDialog.getText(self, title, content, text=default_text)
        return text, ok

    def browse_sound_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择音效文件", "", "音效文件 (*.vsnd_c)")
        if path:
            self.sound_tab.sound_entry.setText(path)
            self.sound_path = path
            self.update_sound_info(path)

    def execute_sound_replace(self):
        if not self.sound_path or not os.path.exists(self.sound_path):
            self.show_error("文件无效", "请先选择有效的音效文件。")
            return
        cs2_path = self.steam_path
        if not cs2_path or not os.path.exists(cs2_path):
            self.show_error("路径缺失", "CS2路径未设置或无效，请先在主页设置。")
            return

        self.animation_manager.animate_button_click(self.sound_tab.execute_btn)

        try:
            replacer = SoundReplacer(cs2_path)
            result = replacer.replace_sound(self.sound_path)

            if result["success"]:
                self.update_recent_activity(f"替换音效: {result['sound_name']}")
                self.show_success("替换成功", f"启动音效已成功替换为 {result['sound_name']}。")
            else:
                self.show_error("替换失败", result['error'])
        except Exception as e:
            self.show_error("严重错误", str(e))

    def update_sound_info(self, sound_path):
        if sound_path and os.path.exists(sound_path):
            sound_name = os.path.splitext(os.path.basename(sound_path))[0]
            filename = os.path.basename(sound_path)
            self.sound_tab.sound_name_label.setText(f"音效名称: {sound_name}")
            self.sound_tab.sound_filename_label.setText(f"文件名: {filename}")
            pass  # 状态标签已删除
        else:
            self.sound_tab.sound_name_label.setText("音效名称: 未选择")
            self.sound_tab.sound_filename_label.setText("文件名: 未选择")
            pass  # 状态标签已删除

    def restore_sound(self):
        cs2_path = self.steam_path
        if not cs2_path or not os.path.exists(cs2_path):
            self.show_error("路径缺失", "CS2路径未设置或无效，请先在主页设置。")
            return

        self.animation_manager.animate_button_click(self.sound_tab.restore_btn)

        try:
            replacer = SoundReplacer(cs2_path)
            result = replacer.restore_sound()

            if result["success"]:
                self.update_recent_activity("还原默认启动音效")
                self.show_success("还原成功", result["message"])
            else:
                self.show_error("还原失败", result["error"])
        except Exception as e:
            self.show_error("严重错误", str(e))

    def load_sound_presets(self):
        self.sound_tab.sound_preset_list.clear()
        sound_presets = self.config_manager.get_presets('sound')
        for i, preset in enumerate(sound_presets):
            item = QListWidgetItem(self.sound_tab.sound_preset_list)
            widget = SoundPresetWidget(preset, self.apply_sound_preset)
            item.setSizeHint(widget.sizeHint())
            self.sound_tab.sound_preset_list.setItemWidget(item, widget)

    def save_sound_preset(self):
        sound_path = self.sound_tab.sound_entry.text()
        if not sound_path or not os.path.exists(sound_path):
            self.show_warning("操作无效", "请先选择一个有效的音效文件。")
            return

        name, ok = self.get_input_dialog("保存音效预设", "输入预设名称:")
        if not ok or not name:
            return

        sound_presets = self.config_manager.get_presets('sound')
        if any(p['name'] == name for p in sound_presets):
            self.show_warning("名称重复", "该预设名称已存在。")
            return

        try:
            sound_filename = os.path.basename(sound_path)
            sound_name_extracted = os.path.splitext(sound_filename)[0]
            self.config_manager.add_preset('sound', name=name, sound_path=sound_path, sound_name=sound_name_extracted, sound_filename=sound_filename)
            self.load_sound_presets()
            self.update_home_status()
            self.update_recent_activity(f"保存音效预设: {name}")
            self.show_success("成功", "音效预设已保存。")
        except Exception as e:
            self.show_error("保存失败", str(e))

    def delete_sound_preset_confirm(self, index):
        title = "确认删除"
        sound_presets = self.config_manager.get_presets('sound')
        content = f"确定要删除音效预设 '{sound_presets[index]['name']}' 吗？"
        if self.show_confirm_dialog(title, content):
            preset_name = sound_presets[index]['name']
            self.config_manager.delete_preset('sound', index)
            self.load_sound_presets()
            self.update_home_status()
            self.update_recent_activity(f"删除音效预设: {preset_name}")

    def apply_sound_preset(self, preset):
        if not os.path.exists(preset["sound_path"]):
            self.show_error("文件丢失", "预设的音效文件已不存在。")
            return

        self.sound_tab.sound_entry.setText(preset["sound_path"])
        self.sound_path = preset["sound_path"]
        self.update_sound_info(preset["sound_path"])

        if self.show_confirm_dialog("确认应用", f"是否立即应用音效预设 '{preset['name']}'？"):
            self.execute_sound_replace()

    def apply_sound_preset_from_item(self, item):
        index = self.sound_tab.sound_preset_list.row(item)
        sound_presets = self.config_manager.get_presets('sound')
        if 0 <= index < len(sound_presets):
            self.apply_sound_preset(sound_presets[index])

    def open_sound_tutorial(self):
        try:
            QDesktopServices.openUrl(QUrl("https://cloverz.top/article/cs2-toolkit%E6%9B%BF%E6%8D%A2cs%E5%BC%80%E5%B1%8F%E9%9F%B3%E6%95%88%E6%95%99%E7%A8%8B"))
            self.update_recent_activity("打开音效替换教程")
        except Exception as e:
            self.show_error("打开失败", f"无法打开教程网站：{str(e)}")
        
    def check_for_updates(self):
        thread = threading.Thread(target=self._update_check_thread, daemon=True)
        thread.start()

    def _update_check_thread(self):
        import requests
        current_version = self.version
        try:
            proxies = {
              "http": None,
              "https": None,
            }
            # 从服务器json文件读取版本信息
            response = requests.get("https://gitee.com/clover23333/CS2-ToolKit/raw/master/version.json", timeout=5, proxies=proxies)
            if response.status_code == 200:
                latest_version_data = response.json()
                latest_version = latest_version_data.get("version")
                if latest_version and latest_version != current_version:
                    self.update_signal_emitter.update_found.emit(latest_version_data)
                elif latest_version and latest_version == current_version:
                    self.update_signal_emitter.update_found.emit({"version": latest_version, "is_latest": True})
        except requests.RequestException as e:
            print(f"检查更新失败: {e}")

    def show_update_dialog(self, version_data):
        # json文件格式
        # {  
        #   "version": "我是最新的版本号(✪ω✪)",
        #   "update_log": "我是更新日志的具体说明(*^▽^*)",
        #   "download_url": "我是下载链接o(´^｀)o"
        # }
        if version_data.get("is_latest", False):
            self.show_info("检查更新", "当前已是最新版本")
            return
        latest_version = version_data.get("version", "N/A")
        update_log = version_data.get("update_log", "无更新日志。")
        download_url = version_data.get("download_url", "")

        title = f"发现新版本: {latest_version}"
        content = f"检测到新版本，是否立即更新？\n\n更新日志:\n{update_log}"
        
        msg_box = MessageBox(title, content, self)
        msg_box.yesButton.setText("立即更新")
        msg_box.cancelButton.setText("忽略此版本")

        if msg_box.exec():
            if download_url:
                QDesktopServices.openUrl(QUrl(download_url))
        else:
            self.show_warning("已忽略更新", "您拒绝更新到最新版本，在此版本中遇到任何问题请勿向作者报告！")

    def closeEvent(self, event):
        self.gsi_manager.stop_server()
        super().closeEvent(event)
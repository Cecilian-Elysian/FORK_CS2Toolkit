import os
import ctypes
import webbrowser
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QUrl, QTimer, Signal, QObject, QPropertyAnimation
from PySide6.QtGui import QPixmap, QColor, QMovie
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class VisualSignals(QObject):
    update_flash = Signal(int)
    show_death = Signal()
    hide_death = Signal()
    minimize_game = Signal()
    restore_game = Signal()
    show_kill_icon = Signal(str)
    open_boss_key_url = Signal(str, int)  # url, delay(ms)
    close_browser = Signal()
    mute_browser = Signal()

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.flash_label = QLabel(self)
        self.flash_label.setScaledContents(True)
        self.flash_label.hide()
        
        self.death_label = QLabel(self)
        self.death_label.setScaledContents(True)
        self.death_label.hide()
        self.death_label.setStyleSheet("background-color: black;")
        
        # 击杀图标控件（静态/GIF）
        self.kill_icon_label = QLabel(self)
        self.kill_icon_label.setScaledContents(True)
        self.kill_icon_label.hide()
        self.kill_icon_movie = None
        self.kill_icon_width = 120
        self.kill_icon_height = 120
        
        # 击杀图标视频控件（MP4/WEBM）
        self.kill_video_widget = QVideoWidget(self)
        self.kill_video_widget.hide()
        self.kill_media_player = QMediaPlayer(self)
        self.kill_audio_output = QAudioOutput(self)
        # 击杀视频通常不需要声音，避免干扰，设置静音
        self.kill_audio_output.setVolume(0)
        self.kill_media_player.setAudioOutput(self.kill_audio_output)
        self.kill_media_player.setVideoOutput(self.kill_video_widget)
        
        self.video_widget = QVideoWidget(self)
        self.video_widget.hide()
        
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        self.flash_image_path = ""
        self.death_media_path = ""
        
        # 淡出动画相关
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_out_step)
        self.current_opacity = 1.0
        
        # 击杀图标定时隐藏
        self.kill_icon_timer = QTimer(self)
        self.kill_icon_timer.timeout.connect(self.hide_kill_icon)
        
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self.kill_icon_opacity_effect = QGraphicsOpacityEffect()
        self.kill_video_opacity_effect = QGraphicsOpacityEffect()
        
        self.kill_icon_label.setGraphicsEffect(self.kill_icon_opacity_effect)
        self.kill_video_widget.setGraphicsEffect(self.kill_video_opacity_effect)
        
        self.kill_icon_opacity_effect.setOpacity(0.0)
        self.kill_video_opacity_effect.setOpacity(0.0)
        
        self.kill_icon_fade_in = QPropertyAnimation(self.kill_icon_opacity_effect, b"opacity")
        self.kill_icon_fade_in.setDuration(300)
        self.kill_icon_fade_in.setStartValue(0.0)
        self.kill_icon_fade_in.setEndValue(1.0)
        
        self.kill_video_fade_in = QPropertyAnimation(self.kill_video_opacity_effect, b"opacity")
        self.kill_video_fade_in.setDuration(300)
        self.kill_video_fade_in.setStartValue(0.0)
        self.kill_video_fade_in.setEndValue(1.0)
        
        self.kill_icon_fade_out = QPropertyAnimation(self.kill_icon_opacity_effect, b"opacity")
        self.kill_icon_fade_out.setDuration(500)
        self.kill_icon_fade_out.setStartValue(1.0)
        self.kill_icon_fade_out.setEndValue(0.0)
        self.kill_icon_fade_out.finished.connect(self._on_kill_icon_fade_out_finished)
        
        self.kill_video_fade_out = QPropertyAnimation(self.kill_video_opacity_effect, b"opacity")
        self.kill_video_fade_out.setDuration(500)
        self.kill_video_fade_out.setStartValue(1.0)
        self.kill_video_fade_out.setEndValue(0.0)
        self.kill_video_fade_out.finished.connect(self._on_kill_video_fade_out_finished)
        
        self.hide()
        
    def _update_geometry_to_game(self):
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Counter-Strike 2")
        if hwnd:
            from ctypes import wintypes
            rect = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            
            pt = wintypes.POINT(0, 0)
            user32.ClientToScreen(hwnd, ctypes.byref(pt))
            
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            # 如果获取到的窗口大小有效，则设置为游戏窗口大小
            if width > 0 and height > 0:
                self.setGeometry(pt.x, pt.y, width, height)
            else:
                screen = self.screen().geometry()
                self.setGeometry(screen)
        else:
            screen = self.screen().geometry()
            self.setGeometry(screen)
            
        self.flash_label.setGeometry(self.rect())
        self.death_label.setGeometry(self.rect())
        self.video_widget.setGeometry(self.rect())
        
        # 击杀图标放在下方正中
        icon_w = self.kill_icon_width
        icon_h = self.kill_icon_height
        icon_x = (self.width() - icon_w) // 2
        icon_y = self.height() - icon_h - 100 # 距离底部100px
        self.kill_icon_label.setGeometry(icon_x, icon_y, icon_w, icon_h)
        self.kill_video_widget.setGeometry(icon_x, icon_y, icon_w, icon_h)

    def set_flash_image(self, path):
        self.flash_image_path = path
        if path and os.path.exists(path):
            self.flash_label.setPixmap(QPixmap(path))
            
    def set_death_media(self, path):
        self.death_media_path = path
        
    def update_flash(self, flash_value):
        if not self.flash_image_path or not os.path.exists(self.flash_image_path):
            self.flash_label.hide()
            self._check_hide()
            return
            
        if flash_value > 0:
            self._update_geometry_to_game()
            # 只要 flashed 为 1，透明度直接设为 1 (100% 显示)
            self.fade_timer.stop()
            self.current_opacity = 1.0
            self.setWindowOpacity(1.0)
            self.flash_label.show()
            self.show()
        else:
            # 当 flashed 变为 0 时，如果图片正在显示，则启动淡出动画
            if not self.flash_label.isHidden() and not self.fade_timer.isActive():
                self.fade_timer.start(50)  # 每 50ms 更新一次透明度
                
    def _fade_out_step(self):
        self.current_opacity -= 0.05  # 每次减少 0.05，约 1 秒淡出
        if self.current_opacity <= 0:
            self.current_opacity = 0
            self.fade_timer.stop()
            self.flash_label.hide()
            self._check_hide()
        self.setWindowOpacity(self.current_opacity)
            
    def show_death(self):
        if not self.death_media_path or not os.path.exists(self.death_media_path):
            return
            
        self._update_geometry_to_game()
        self.setWindowOpacity(1.0)
        self.show()
        
        if self.death_media_path.lower().endswith(('.mp4', '.webm', '.avi')):
            self.video_widget.show()
            self.media_player.setSource(QUrl.fromLocalFile(self.death_media_path))
            self.media_player.play()
        else:
            self.death_label.setPixmap(QPixmap(self.death_media_path))
            self.death_label.show()
            
    def hide_death(self):
        self.death_label.hide()
        self.video_widget.hide()
        self.media_player.stop()
        self._check_hide()
        
    def show_kill_icon(self, path):
        if not path or not os.path.exists(path):
            return
        self._update_geometry_to_game()
        
        # 停止可能正在运行的淡出动画和定时器
        self.kill_icon_fade_out.stop()
        self.kill_video_fade_out.stop()
        self.kill_icon_timer.stop()
        
        self.setWindowOpacity(1.0)
        self.show()
        
        is_video = path.lower().endswith(('.mp4', '.webm', '.avi'))
        is_gif = path.lower().endswith('.gif')
        
        if is_video:
            self.kill_icon_label.hide()
            if self.kill_icon_movie:
                self.kill_icon_movie.stop()
            
            self.kill_media_player.setSource(QUrl.fromLocalFile(path))
            self.kill_video_widget.show()
            self.kill_media_player.play()
            self.kill_video_fade_in.start()
        elif is_gif:
            self.kill_video_widget.hide()
            self.kill_media_player.stop()
            
            if self.kill_icon_movie:
                self.kill_icon_movie.stop()
            
            self.kill_icon_movie = QMovie(path)
            self.kill_icon_label.setMovie(self.kill_icon_movie)
            self.kill_icon_movie.start()
            self.kill_icon_label.show()
            self.kill_icon_fade_in.start()
        else:
            self.kill_video_widget.hide()
            self.kill_media_player.stop()
            
            if self.kill_icon_movie:
                self.kill_icon_movie.stop()
                
            self.kill_icon_label.setPixmap(QPixmap(path))
            self.kill_icon_label.show()
            self.kill_icon_fade_in.start()
        
        # 显示3秒后触发淡出
        self.kill_icon_timer.start(3000)

    def hide_kill_icon(self):
        self.kill_icon_timer.stop()
        if not self.kill_icon_label.isHidden():
            self.kill_icon_fade_out.start()
        if not self.kill_video_widget.isHidden():
            self.kill_video_fade_out.start()

    def _on_kill_icon_fade_out_finished(self):
        self.kill_icon_label.hide()
        if self.kill_icon_movie:
            self.kill_icon_movie.stop()
        self._check_hide()
        
    def _on_kill_video_fade_out_finished(self):
        self.kill_video_widget.hide()
        self.kill_media_player.stop()
        self._check_hide()

    def _check_hide(self):
        if self.flash_label.isHidden() and self.death_label.isHidden() and self.video_widget.isHidden() and self.kill_icon_label.isHidden() and self.kill_video_widget.isHidden():
            self.hide()


class VisualHandler(QObject):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.signals = VisualSignals()
        
        self.overlay = OverlayWindow()
        self.signals.update_flash.connect(self.overlay.update_flash)
        self.signals.show_death.connect(self.overlay.show_death)
        self.signals.hide_death.connect(self.overlay.hide_death)
        self.signals.show_kill_icon.connect(self.overlay.show_kill_icon)
        
        self.signals.minimize_game.connect(self._minimize_cs2)
        self.signals.restore_game.connect(self._restore_cs2)
        self.signals.open_boss_key_url.connect(self._open_boss_key_url)
        self.signals.close_browser.connect(self._close_browser)
        self.signals.mute_browser.connect(self._mute_browser)
        
        self.is_flashed = False
        self.is_dead = False
        self._last_round_kills = -1
        
        self._update_config()
        
    def _update_config(self):
        config = self.config_manager.get('visual', {})
        self.flash_enabled = config.get('flash_enabled', False)
        self.flash_path = config.get('flash_path', '')
        self.overlay.set_flash_image(self.flash_path)
        
        self.death_media_enabled = config.get('death_media_enabled', False)
        self.death_media_path = config.get('death_media_path', '')
        self.overlay.set_death_media(self.death_media_path)
        
        self.boss_key_enabled = config.get('boss_key_enabled', False)
        self.boss_key_url = config.get('boss_key_url', 'https://www.baidu.com')
        self.boss_key_delay = config.get('boss_key_delay', 0)
        self.boss_key_action = config.get('boss_key_action', 'none')
        
        self.kill_icon_enabled = config.get('kill_icon_enabled', False)
        self.kill_icon_is_advanced = config.get('kill_icon_is_advanced', False)
        self.kill_icon_path = config.get('kill_icon_path', '')
        self.kill_icons_1_5 = config.get('kill_icons_1_5', [{} for _ in range(5)])
        self.overlay.kill_icon_width = config.get('kill_icon_width', 120)
        self.overlay.kill_icon_height = config.get('kill_icon_height', 120)
        
    def process_gsi(self, game_state: dict):
        self._update_config()
        
        player = game_state.get('player', {})
        if not player:
            return
            
        state = player.get('state', {})
        activity = player.get('activity', '')
        spectarget = player.get('spectarget')
        
        # 如果是观战状态，不处理闪光和切屏
        # 观战检测逻辑需要更严谨，防止被他人闪光或死亡影响
        has_valid_team = player.get('team', '') in ['T', 'CT']
        provider = game_state.get('provider', {})
        provider_steamid = provider.get('steamid')
        player_steamid = player.get('steamid')
        
        is_observing = False
        if provider_steamid and player_steamid and provider_steamid != player_steamid:
            is_observing = True
        elif spectarget is not None or activity == 'spectating' or activity != 'playing' or not has_valid_team:
            is_observing = True
        
        # 1. 闪光弹处理
        if self.flash_enabled and not is_observing:
            # CS2 GSI 传入的 flashed 值是 0 或 1
            flash_value = state.get('flashed', 0)
            
            if flash_value > 0:
                print(f"[视觉效果] 接收到闪白数据: flashed={flash_value}")
            
            # 直接触发更新信号
            self.signals.update_flash.emit(flash_value)
            
        # 2. 死亡处理
        health = state.get('health', 100)
        round_info = game_state.get('round', {})
        phase = round_info.get('phase', '')
        
        # 观战状态下直接清空死亡显示，不处理死亡逻辑
        if is_observing:
            if self.is_dead:
                self.is_dead = False
                if self.death_media_enabled:
                    self.signals.hide_death.emit()
            self._last_phase = phase
            return
            
        # 只在非观战状态下或刚死时处理
        if health == 0 and not self.is_dead:
            self.is_dead = True
            
            if self.death_media_enabled:
                self.signals.show_death.emit()
                
            if self.boss_key_enabled and not is_observing:
                self.signals.minimize_game.emit()
                self.signals.open_boss_key_url.emit(self.boss_key_url, self.boss_key_delay * 1000)
                
        elif health > 0 and self.is_dead:
            self.is_dead = False
            if self.death_media_enabled:
                self.signals.hide_death.emit()
                
        # 3. 回合重置恢复游戏和连杀重置
        if phase in ['freezetime', 'live'] and self.is_dead and health > 0:
            self.is_dead = False
            if self.boss_key_enabled:
                self.signals.restore_game.emit()
                if self.boss_key_action == 'close':
                    self.signals.close_browser.emit()
                elif self.boss_key_action == 'mute':
                    self.signals.mute_browser.emit()
            if self.death_media_enabled:
                self.signals.hide_death.emit()
                
        if phase == 'freezetime' and getattr(self, '_last_phase', '') != 'freezetime':
            self._last_round_kills = 0
        
        # 强制在复活后恢复
        if health > 0 and phase == 'freezetime' and getattr(self, '_last_phase', '') != 'freezetime':
            if self.boss_key_enabled:
                self.signals.restore_game.emit()
                if self.boss_key_action == 'close':
                    self.signals.close_browser.emit()
                elif self.boss_key_action == 'mute':
                    self.signals.mute_browser.emit()
                
        # 4. 击杀图标处理
        if self.kill_icon_enabled and not is_observing:
            current_round_kills = state.get('round_kills', 0)
            
            if getattr(self, '_last_round_kills', -1) == -1:
                self._last_round_kills = current_round_kills
                
            if current_round_kills > self._last_round_kills:
                self._last_round_kills = current_round_kills
                
                # 决定显示的图标
                icon_to_show = ""
                if self.kill_icon_is_advanced:
                    idx = min(current_round_kills - 1, 4)
                    icon_to_show = self.kill_icons_1_5[idx].get('path', '')
                    if not icon_to_show or not os.path.exists(icon_to_show):
                        icon_to_show = self.kill_icon_path
                else:
                    icon_to_show = self.kill_icon_path
                    
                if icon_to_show and os.path.exists(icon_to_show):
                    self.signals.show_kill_icon.emit(icon_to_show)
            elif current_round_kills < self._last_round_kills:
                self._last_round_kills = current_round_kills
        elif is_observing:
            self._last_round_kills = state.get('round_kills', 0)
        
        self._last_phase = phase

    def _minimize_cs2(self):
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Counter-Strike 2")
        if hwnd:
            user32.ShowWindow(hwnd, 6) # SW_MINIMIZE

    def _restore_cs2(self):
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Counter-Strike 2")
        if hwnd:
            user32.ShowWindow(hwnd, 9) # SW_RESTORE
            user32.SetForegroundWindow(hwnd)

    def _open_boss_key_url(self, url, delay_ms):
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, lambda: webbrowser.open(url))
        else:
            webbrowser.open(url)
            
    def _close_browser(self):
        import subprocess
        # 强制关闭常见的浏览器进程
        browsers = ["msedge.exe", "chrome.exe", "firefox.exe", "360se.exe", "iexplore.exe", "sogouexplorer.exe"]
        for b in browsers:
            subprocess.run(["taskkill", "/F", "/IM", b], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
    def _mute_browser(self):
        try:
            from pycaw.pycaw import AudioUtilities
            sessions = AudioUtilities.GetAllSessions()
            browsers = ["msedge.exe", "chrome.exe", "firefox.exe", "360se.exe", "iexplore.exe", "sogouexplorer.exe"]
            for session in sessions:
                volume = session.SimpleAudioVolume
                if session.Process and session.Process.name() in browsers:
                    volume.SetMute(1, None)
        except Exception as e:
            print(f"静音浏览器失败: {e}")

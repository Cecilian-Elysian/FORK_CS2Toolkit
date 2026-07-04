import os
import ctypes
import webbrowser
import random
import json
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
    minimize_browser = Signal()
    pause_media = Signal()

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.flash_label = QLabel(self)
        self.flash_label.setAlignment(Qt.AlignCenter)
        self.flash_label.hide()
        
        self.death_label = QLabel(self)
        self.death_label.setAlignment(Qt.AlignCenter)
        self.death_label.hide()
        self.death_label.setStyleSheet("background-color: black;")
        
        # 击杀图标控件（静态/GIF）
        self.kill_icon_label = QLabel(self)
        self.kill_icon_label.setScaledContents(True)
        self.kill_icon_label.hide()
        self.kill_icon_movie = None
        self.kill_icon_width = 120
        self.kill_icon_height = 120
        self.kill_icon_bottom = 100
        
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
        self.flash_scale_mode = "stretch"
        self._flash_folder_files = []
        self._flash_cached_source = ""
        self._flash_cached_pixmap = QPixmap()
        self.death_media_path = ""
        self.death_scale_mode = "stretch"
        
        # 淡出动画相关
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_out_step)
        self.current_opacity = 1.0
        
        # 击杀图标定时隐藏
        self.kill_icon_timer = QTimer(self)
        self.kill_icon_timer.timeout.connect(self.hide_kill_icon)
        
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self.flash_opacity_effect = QGraphicsOpacityEffect()
        self.kill_icon_opacity_effect = QGraphicsOpacityEffect()
        self.kill_video_opacity_effect = QGraphicsOpacityEffect()
        
        self.flash_label.setGraphicsEffect(self.flash_opacity_effect)
        self.kill_icon_label.setGraphicsEffect(self.kill_icon_opacity_effect)
        self.kill_video_widget.setGraphicsEffect(self.kill_video_opacity_effect)
        
        self.flash_opacity_effect.setOpacity(0.0)
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
        
        # 重新应用缩放模式，因为窗口大小变了
        if not self.flash_label.isHidden():
            self._update_label_pixmap(self.flash_label, self.flash_image_path, self.flash_scale_mode)
        if not self.death_label.isHidden() and not self.death_media_path.lower().endswith(('.mp4', '.webm', '.avi')):
            self._update_label_pixmap(self.death_label, self.death_media_path, self.death_scale_mode)
        
        # 击杀图标放在下方正中
        icon_w = self.kill_icon_width
        icon_h = self.kill_icon_height
        icon_x = (self.width() - icon_w) // 2
        icon_y = self.height() - icon_h - self.kill_icon_bottom
        self.kill_icon_label.setGeometry(icon_x, icon_y, icon_w, icon_h)
        self.kill_video_widget.setGeometry(icon_x, icon_y, icon_w, icon_h)

    def set_flash_image(self, path, scale_mode="stretch"):
        changed = path != self.flash_image_path or scale_mode != self.flash_scale_mode
        self.flash_image_path = path
        self.flash_scale_mode = scale_mode
        if not changed:
            return

        self._flash_folder_files = []
        self._flash_cached_source = ""
        self._flash_cached_pixmap = QPixmap()

        if path and os.path.isdir(path):
            valid_exts = {'.png', '.jpg', '.jpeg', '.bmp'}
            self._flash_folder_files = [
                os.path.join(path, f)
                for f in os.listdir(path)
                if os.path.splitext(f)[1].lower() in valid_exts
            ]
        elif path and os.path.isfile(path):
            self._flash_cached_source = path
            self._flash_cached_pixmap = QPixmap(path)
            
    def set_death_media(self, path, scale_mode="stretch"):
        self.death_media_path = path
        self.death_scale_mode = scale_mode
        
    def _update_label_pixmap(self, label, image_path, scale_mode):
        if not image_path or not os.path.exists(image_path):
            return
            
        if os.path.isdir(image_path):
            valid_exts = {'.png', '.jpg', '.jpeg', '.bmp'}
            files = [os.path.join(image_path, f) for f in os.listdir(image_path) if os.path.splitext(f)[1].lower() in valid_exts]
            if not files:
                return
            image_path = random.choice(files)
            
        pixmap = QPixmap(image_path)
        if scale_mode == 'stretch':
            label.setScaledContents(True)
            label.setPixmap(pixmap)
        else:
            label.setScaledContents(False)
            if scale_mode == 'keep_aspect_crop':
                aspect_mode = Qt.KeepAspectRatioByExpanding
            else:
                aspect_mode = Qt.KeepAspectRatio
                
            # If the label has a valid size, scale the pixmap
            if label.width() > 0 and label.height() > 0:
                scaled_pixmap = pixmap.scaled(label.size(), aspect_mode, Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
            else:
                label.setPixmap(pixmap)

    def _set_label_pixmap_from_pixmap(self, label, pixmap, scale_mode):
        if pixmap.isNull():
            return

        if scale_mode == 'stretch':
            label.setScaledContents(True)
            label.setPixmap(pixmap)
            return

        label.setScaledContents(False)
        if scale_mode == 'keep_aspect_crop':
            aspect_mode = Qt.KeepAspectRatioByExpanding
        else:
            aspect_mode = Qt.KeepAspectRatio

        if label.width() > 0 and label.height() > 0:
            scaled_pixmap = pixmap.scaled(label.size(), aspect_mode, Qt.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
        else:
            label.setPixmap(pixmap)

    def _prepare_flash_pixmap(self):
        if self._flash_folder_files:
            chosen = random.choice(self._flash_folder_files)
            pixmap = QPixmap(chosen)
            return chosen, pixmap
        return self._flash_cached_source, self._flash_cached_pixmap
        
    def update_flash(self, flash_value):
        if not self.flash_image_path or not os.path.exists(self.flash_image_path):
            self.fade_timer.stop()
            self.current_opacity = 0.0
            self.flash_opacity_effect.setOpacity(0.0)
            self.flash_label.hide()
            self.flash_label.setPixmap(QPixmap())
            self._check_hide()
            return
            
        if flash_value > 0:
            self._update_geometry_to_game()

            _, pixmap = self._prepare_flash_pixmap()
            self._set_label_pixmap_from_pixmap(self.flash_label, pixmap, self.flash_scale_mode)
                
            # 只要 flashed 为 1，透明度直接设为 1 (100% 显示)
            self.fade_timer.stop()
            self.current_opacity = 1.0
            self.flash_opacity_effect.setOpacity(1.0)
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
            self.flash_opacity_effect.setOpacity(0.0)
            self.flash_label.hide()
            self.flash_label.setPixmap(QPixmap()) # 释放闪光图内存
            self._check_hide()
            return
        self.flash_opacity_effect.setOpacity(self.current_opacity)
            
    def show_death(self):
        if not self.death_media_path or not os.path.exists(self.death_media_path):
            return
            
        self._update_geometry_to_game()
        self.setWindowOpacity(1.0)
        self.show()
        
        if self.death_media_path.lower().endswith(('.mp4', '.webm', '.avi')):
            # QVideoWidget 默认自带等比例拉伸，如果是拉伸拉满需要设置 aspect ratio mode
            if self.death_scale_mode == 'stretch':
                self.video_widget.setAspectRatioMode(Qt.IgnoreAspectRatio)
            elif self.death_scale_mode == 'keep_aspect_crop':
                self.video_widget.setAspectRatioMode(Qt.KeepAspectRatioByExpanding)
            else:
                self.video_widget.setAspectRatioMode(Qt.KeepAspectRatio)
                
            self.video_widget.show()
            self.media_player.setSource(QUrl.fromLocalFile(self.death_media_path))
            self.media_player.play()
        else:
            self._update_label_pixmap(self.death_label, self.death_media_path, self.death_scale_mode)
            self.death_label.show()
            
    def hide_death(self):
        self.death_label.hide()
        self.death_label.setPixmap(QPixmap()) # 释放静态图内存
        self.video_widget.hide()
        self.media_player.stop()
        self.media_player.setSource(QUrl())  # 释放内存
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
            self.kill_icon_label.setMovie(None) # 释放GIF内存
        self.kill_icon_label.setPixmap(QPixmap()) # 释放静态图内存
        self._check_hide()

    def _on_kill_video_fade_out_finished(self):
        self.kill_video_widget.hide()
        self.kill_media_player.stop()
        self.kill_media_player.setSource(QUrl()) # 释放视频内存
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
        self.signals.minimize_browser.connect(self._minimize_browser)
        self.signals.pause_media.connect(self._pause_media)
        
        self.is_flashed = False
        self.is_dead = False
        self._boss_key_triggered = False
        self._browser_opened = False
        self._browser_muted = False
        self._last_match_kills = -1
        self._round_start_kills = 0
        self._visual_config_signature = None
        
        self._update_config(force=True)
        
    def _update_config(self, force=False):
        config = self.config_manager.get('visual', {})
        signature = json.dumps(config, ensure_ascii=False, sort_keys=True)
        if not force and signature == self._visual_config_signature:
            return
        self._visual_config_signature = signature

        self.flash_enabled = config.get('flash_enabled', False)
        self.flash_path = config.get('flash_path', '')
        self.overlay.set_flash_image(self.flash_path, config.get('flash_scale_mode', 'stretch'))
        
        self.death_media_enabled = config.get('death_media_enabled', False)
        self.death_media_path = config.get('death_media_path', '')
        self.overlay.set_death_media(self.death_media_path, config.get('death_scale_mode', 'stretch'))
        
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
        self.overlay.kill_icon_bottom = config.get('kill_icon_bottom', 100)
        
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
            flash_active = state.get('flashed', 0) > 0
            if flash_active != self.is_flashed:
                self.is_flashed = flash_active
                self.signals.update_flash.emit(1 if flash_active else 0)
        elif self.is_flashed:
            self.is_flashed = False
            self.signals.update_flash.emit(0)
            
        # 2. 死亡与复活处理
        health = state.get('health', 100)
        round_info = game_state.get('round', {})
        phase = round_info.get('phase', '')
        
        # 处理死亡显示和 Boss Key 触发
        if not is_observing and health == 0 and not self.is_dead:
            self.is_dead = True
            if self.death_media_enabled:
                self.signals.show_death.emit()
                
            if self.boss_key_enabled:
                self._boss_key_triggered = True
                self.signals.open_boss_key_url.emit(self.boss_key_url, self.boss_key_delay * 1000)
                
        elif health > 0 and self.is_dead:
            self.is_dead = False
            if self.death_media_enabled:
                self.signals.hide_death.emit()

        # 观战状态下强制清空死亡UI，但千万不能重置 is_dead = False，否则会打断 Boss Key 的状态判定
        if is_observing and self.is_dead:
            if self.death_media_enabled:
                self.signals.hide_death.emit()

        # 3. 回合重置恢复游戏和连杀重置
        # 触发条件：玩家处于非观战状态，且已存活，且之前触发了 Boss Key 或被静音过
        if not is_observing and health > 0 and phase in ['freezetime', 'live']:
            if getattr(self, '_boss_key_triggered', False) or getattr(self, '_browser_muted', False):
                self._boss_key_triggered = False
                if self.boss_key_enabled:
                    if self.boss_key_action == 'close':
                        self.signals.close_browser.emit()
                        self._browser_opened = False
                    elif self.boss_key_action == 'pause':
                        # 发送按键前先判断当前系统是否在播放音频
                        # 只有当系统正在发声时，我们才发送“暂停”指令
                        is_playing = self._is_audio_playing()
                        if getattr(self, '_browser_muted', False) and is_playing:
                            self.signals.pause_media.emit()
                        self._minimize_browser()
                    
                    self.signals.restore_game.emit()
                
                # 非常重要：重置静音标记，防止无限触发，必须放在 if boss_key_enabled 外面或最后
                self._browser_muted = False
                        
        if phase == 'freezetime' and getattr(self, '_last_phase', '') != 'freezetime':
            # Round reset
            match_stats = player.get('match_stats', {})
            self._round_start_kills = match_stats.get('kills', 0)
                
        # 4. 击杀图标处理
        if self.kill_icon_enabled and not is_observing:
            match_stats = player.get('match_stats', {})
            current_match_kills = match_stats.get('kills', 0)
            
            if self._last_match_kills == -1:
                self._last_match_kills = current_match_kills
                self._round_start_kills = current_match_kills
                
            if current_match_kills > self._last_match_kills:
                self._last_match_kills = current_match_kills
                current_round_kills = current_match_kills - self._round_start_kills
                
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
            elif current_match_kills < self._last_match_kills:
                self._last_match_kills = current_match_kills
        elif is_observing:
            match_stats = player.get('match_stats', {})
            self._last_match_kills = match_stats.get('kills', 0)
        
        self._last_phase = phase

    def _minimize_cs2(self):
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Counter-Strike 2")
        if hwnd:
            # 最小化之前，先解除鼠标锁定（如果是独占模式可能需要）
            user32.ClipCursor(None)
            # 先尝试通过发送 WM_SYSCOMMAND SC_MINIMIZE 消息来最小化，这通常更平滑
            user32.PostMessageW(hwnd, 0x0112, 0xF020, 0)
            
            # 为了确保全屏模式下也能可靠最小化并释放焦点，补充一个 ShowWindow 最小化非激活
            # SW_SHOWMINNOACTIVE = 7
            user32.ShowWindow(hwnd, 7)

    def _restore_cs2(self):
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Counter-Strike 2")
        if hwnd:
            # 强制解除当前可能的其他窗口置顶状态
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            
            # 尝试附加线程输入
            current_thread = kernel32.GetCurrentThreadId()
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd:
                fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
                if fg_thread != current_thread:
                    user32.AttachThreadInput(current_thread, fg_thread, True)
                    user32.ShowWindow(hwnd, 9) # SW_RESTORE
                    user32.SetForegroundWindow(hwnd)
                    user32.AttachThreadInput(current_thread, fg_thread, False)
                else:
                    user32.ShowWindow(hwnd, 9)
                    user32.SetForegroundWindow(hwnd)
            else:
                user32.ShowWindow(hwnd, 9)
                user32.SetForegroundWindow(hwnd)

    def _open_boss_key_url(self, url, delay_ms):
        # 确保 URL 有 scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        def _action():
            # 如果在延迟期间玩家已经复活，则取消切屏
            if not getattr(self, '_boss_key_triggered', False):
                return
            
            self._minimize_cs2()
            
            # 严格控制：只要在这局游戏运行期间打开过一次浏览器，就绝对不再调用 openUrl 弹新标签
            if not getattr(self, '_browser_opened', False):
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(QUrl(url))
                self._browser_opened = True
            else:
                # 尝试将已有的浏览器窗口置于前台
                success = self._activate_browser_window()
                if not success:
                    # 如果系统里确实没找到任何浏览器窗口（可能用户手动关掉了），则重新打开
                    from PySide6.QtGui import QDesktopServices
                    QDesktopServices.openUrl(QUrl(url))
                    self._browser_opened = True
            
            if self.boss_key_action == 'pause':
                # 在切出游戏时发送暂停/播放媒体键
                # 只有当系统没有发声（处于暂停状态）时，我们才发送“播放”指令
                is_playing = self._is_audio_playing()
                if not is_playing:
                    self._pause_media()
                # 必须标记为 True，这样在新回合开始时程序才知道需要再发一次按键恢复播放
                self._browser_muted = True
            
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, _action)
        else:
            _action()
            
    def _activate_browser_window(self):
        try:
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            def get_process_name(pid):
                # 使用 PROCESS_QUERY_LIMITED_INFORMATION (0x1000) 替代 PROCESS_VM_READ，避免权限不足导致获取不到进程名
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if hProcess:
                    exe_name = ctypes.create_unicode_buffer(260)
                    size = wintypes.DWORD(260)
                    if kernel32.QueryFullProcessImageNameW(hProcess, 0, exe_name, ctypes.byref(size)):
                        kernel32.CloseHandle(hProcess)
                        return exe_name.value
                    kernel32.CloseHandle(hProcess)
                return ""
            
            found = False
            
            def enum_windows_proc(hwnd, lParam):
                nonlocal found
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        class_name = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(hwnd, class_name, 256)
                        cname = class_name.value
                        
                        is_browser = False
                        # 通过类名快速匹配大多数主流浏览器
                        if cname in ['Chrome_WidgetWin_1', 'MozillaWindowClass']:
                            # 但是要排除掉 QQ 和 微信 等也使用了 Chromium 内核的软件
                            pid = wintypes.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            exe_path = get_process_name(pid.value).lower()
                            exe_name = os.path.basename(exe_path)
                            
                            # 只有当它确实是浏览器进程时才判定为浏览器
                            browsers = ['msedge.exe', 'chrome.exe', 'firefox.exe', '360se.exe', 'iexplore.exe', 'sogouexplorer.exe', 'browser.exe', 'yandex.exe', 'opera.exe', 'brave.exe']
                            if any(b in exe_name for b in browsers):
                                is_browser = True
                        else:
                            # 兜底：通过进程名匹配
                            pid = wintypes.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            exe_path = get_process_name(pid.value).lower()
                            exe_name = os.path.basename(exe_path)
                            
                            browsers = ['msedge.exe', 'chrome.exe', 'firefox.exe', '360se.exe', 'iexplore.exe', 'sogouexplorer.exe', 'browser.exe', 'yandex.exe', 'opera.exe', 'brave.exe']
                            
                            if any(b in exe_name for b in browsers):
                                is_browser = True
                        
                        if is_browser:
                            # 过滤掉一些幽灵窗口 (ToolWindow)
                            GWL_EXSTYLE = -20
                            WS_EX_TOOLWINDOW = 0x00000080
                            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                            if not (style & WS_EX_TOOLWINDOW):
                                # 绕过前台窗口限制
                                current_thread = kernel32.GetCurrentThreadId()
                                fg_hwnd = user32.GetForegroundWindow()
                                
                                # 使用更安全的方式定义 WINDOWPLACEMENT
                                class WINDOWPLACEMENT(ctypes.Structure):
                                    _fields_ = [
                                        ("length", wintypes.UINT),
                                        ("flags", wintypes.UINT),
                                        ("showCmd", wintypes.UINT),
                                        ("ptMinPosition", wintypes.POINT),
                                        ("ptMaxPosition", wintypes.POINT),
                                        ("rcNormalPosition", wintypes.RECT)
                                    ]
                                
                                # 我们这里获取窗口原本的显示状态
                                placement = WINDOWPLACEMENT()
                                placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                                user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
                                
                                # SW_SHOWMAXIMIZED = 3, SW_RESTORE = 9, WPF_RESTORETOMAXIMIZED = 2
                                # 如果当前是最大化(3)，或者最小化之前是最大化(flags & 2)，则恢复为最大化
                                WPF_RESTORETOMAXIMIZED = 0x0002
                                if placement.showCmd == 3 or (placement.flags & WPF_RESTORETOMAXIMIZED):
                                    show_cmd = 3
                                else:
                                    show_cmd = 9
                                
                                if fg_hwnd:
                                    fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
                                    if fg_thread != current_thread:
                                        user32.AttachThreadInput(current_thread, fg_thread, True)
                                        user32.ShowWindow(hwnd, show_cmd)
                                        user32.SetForegroundWindow(hwnd)
                                        user32.AttachThreadInput(current_thread, fg_thread, False)
                                        found = True
                                        return False # 停止枚举
                                
                                user32.ShowWindow(hwnd, show_cmd)
                                user32.SetForegroundWindow(hwnd)
                                found = True
                                return False # 停止枚举
                return True
                
            EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
            return found
        except Exception as e:
            print(f"激活浏览器窗口失败: {e}")
            return False
            
    def _minimize_browser(self):
        try:
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            def get_process_name(pid):
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if hProcess:
                    exe_name = ctypes.create_unicode_buffer(260)
                    size = wintypes.DWORD(260)
                    if kernel32.QueryFullProcessImageNameW(hProcess, 0, exe_name, ctypes.byref(size)):
                        kernel32.CloseHandle(hProcess)
                        return exe_name.value
                    kernel32.CloseHandle(hProcess)
                return ""
            
            def enum_windows_proc(hwnd, lParam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        class_name = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(hwnd, class_name, 256)
                        cname = class_name.value
                        
                        is_browser = False
                        if cname in ['Chrome_WidgetWin_1', 'MozillaWindowClass']:
                            pid = wintypes.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            exe_path = get_process_name(pid.value).lower()
                            exe_name = os.path.basename(exe_path)
                            browsers = ['msedge.exe', 'chrome.exe', 'firefox.exe', '360se.exe', 'iexplore.exe', 'sogouexplorer.exe', 'browser.exe', 'yandex.exe', 'opera.exe', 'brave.exe']
                            if any(b in exe_name for b in browsers):
                                is_browser = True
                        else:
                            pid = wintypes.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            exe_path = get_process_name(pid.value).lower()
                            exe_name = os.path.basename(exe_path)
                            browsers = ['msedge.exe', 'chrome.exe', 'firefox.exe', '360se.exe', 'iexplore.exe', 'sogouexplorer.exe', 'browser.exe', 'yandex.exe', 'opera.exe', 'brave.exe']
                            if any(b in exe_name for b in browsers):
                                is_browser = True
                                
                        if is_browser:
                            user32.PostMessageW(hwnd, 0x0112, 0xF020, 0) # WM_SYSCOMMAND, SC_MINIMIZE
                return True
                
            EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
        except Exception as e:
            print(f"最小化浏览器失败: {e}")

    def _pause_media(self):
        try:
            # 模拟按下键盘的 播放/暂停 媒体键 (VK_MEDIA_PLAY_PAUSE = 0xB3)
            user32 = ctypes.windll.user32
            user32.keybd_event(0xB3, 0, 0, 0) # Key Down
            user32.keybd_event(0xB3, 0, 2, 0) # Key Up
        except Exception as e:
            print(f"发送媒体暂停键失败: {e}")
            
    def _is_audio_playing(self):
        """检测目标浏览器是否真的在输出音频，避免“手动暂停后仍被误判为播放中”"""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
            sessions = AudioUtilities.GetAllSessions()

            # 只关心主流浏览器的真实输出音量，忽略 QQ/系统提示音等其他软件
            target_browsers = [
                'msedge.exe', 'chrome.exe', 'firefox.exe', '360se.exe',
                'iexplore.exe', 'sogouexplorer.exe', 'browser.exe',
                'yandex.exe', 'opera.exe', 'brave.exe'
            ]

            for session in sessions:
                if not session.Process:
                    continue

                process_name = session.Process.name().lower()
                if not any(browser == process_name for browser in target_browsers):
                    continue

                try:
                    meter = session._ctl.QueryInterface(IAudioMeterInformation)
                    peak_value = meter.GetPeakValue()
                except Exception:
                    peak_value = 0.0

                # 只有浏览器会话存在真实音频输出时，才认为媒体正在播放
                if peak_value > 0.001:
                    return True

            return False
        except Exception as e:
            print(f"音频状态检测失败: {e}")
            return False
            
    def _close_browser(self):
        import subprocess
        # 强制关闭常见的浏览器进程
        browsers = ["msedge.exe", "chrome.exe", "firefox.exe", "360se.exe", "iexplore.exe", "sogouexplorer.exe"]
        for b in browsers:
            subprocess.run(["taskkill", "/F", "/IM", b], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

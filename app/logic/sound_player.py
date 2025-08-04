from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject
import os

class SoundPlayer:
    """
    使用 QtMultimedia 播放音效的封装类，支持同时播放多个音效。
    """
    def __init__(self):
        self._players = []  # 存储多个播放器实例
        self._max_players = 10  # 最大同时播放数量

    def play_sound(self, sound_path, volume=None):
        """
        播放指定路径的音效文件。
        支持 mp3, wav 等 QtMultimedia 支持的格式。
        每次播放都会创建新的播放器实例，支持同时播放多个音效。
        :param sound_path: 音效文件路径
        :param volume: 音量 (0-100)，如果为None则使用默认音量50%
        """
        if not os.path.exists(sound_path):
            print(f"音效文件不存在: {sound_path}")
            return

        # 清理已完成播放的播放器
        self._cleanup_finished_players()
        
        # 如果播放器数量超过限制，移除最旧的
        if len(self._players) >= self._max_players:
            oldest_player = self._players.pop(0)
            oldest_player['player'].stop()
            oldest_player['player'].deleteLater()
            oldest_player['audio_output'].deleteLater()

        # 创建新的播放器实例
        player = QMediaPlayer()
        audio_output = QAudioOutput()
        player.setAudioOutput(audio_output)
        
        # 设置音量
        if volume is not None:
            audio_output.setVolume(volume / 100.0)
        else:
            audio_output.setVolume(0.5)  # 默认50%音量
        
        # 播放完成后自动清理
        player.mediaStatusChanged.connect(lambda status: self._on_media_status_changed(player, status))
        
        # 存储播放器引用
        player_info = {
            'player': player,
            'audio_output': audio_output,
            'finished': False
        }
        self._players.append(player_info)
        
        # 播放音效
        url = QUrl.fromLocalFile(sound_path)
        player.setSource(url)
        player.play()
        
        print(f"[音效播放] 创建新播放器播放: {sound_path}, 当前活跃播放器数量: {len(self._players)}")
    
    def _on_media_status_changed(self, player, status):
        # 媒体状态改变时的回调
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 标记播放器为已完成
            for player_info in self._players:
                if player_info['player'] == player:
                    player_info['finished'] = True
                    break
    
    def _cleanup_finished_players(self):
        # 清理已完成播放的播放器
        finished_players = [p for p in self._players if p['finished']]
        for player_info in finished_players:
            player_info['player'].deleteLater()
            player_info['audio_output'].deleteLater()
            self._players.remove(player_info)
        
        if finished_players:
            print(f"[音效播放] 清理了 {len(finished_players)} 个已完成的播放器")
    
    def set_volume(self, volume):
        """
        设置音量。
        :param volume: 0到100的整数。
        """
        if 0 <= volume <= 100:
            # 为所有活跃的播放器设置音量
            for player_info in self._players:
                if not player_info['finished']:
                    player_info['audio_output'].setVolume(volume / 100.0)
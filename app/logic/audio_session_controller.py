class AudioSessionController:
    def __init__(self):
        self._reduced_sessions = {}

    def reduce_process_volume(self, process_names, target_percent):
        try:
            from pycaw.pycaw import AudioUtilities
        except Exception:
            return False, "音量控制依赖不可用，请检查 pycaw 环境。"

        if not process_names:
            return False, "未指定需要控制音量的进程。"

        target_volume = max(0.0, min(float(target_percent) / 100.0, 1.0))
        lowered = 0
        normalized_names = {name.lower() for name in process_names}

        try:
            for session in AudioUtilities.GetAllSessions():
                if not session.Process:
                    continue

                process_name = session.Process.name().lower()
                if process_name not in normalized_names:
                    continue

                volume = session.SimpleAudioVolume
                key = f"{process_name}:{session.Process.pid}"
                if key not in self._reduced_sessions:
                    self._reduced_sessions[key] = volume.GetMasterVolume()
                volume.SetMasterVolume(target_volume, None)
                lowered += 1
        except Exception as e:
            return False, f"调整游戏音量失败：{e}"

        if lowered == 0:
            return False, "未找到可控制的游戏音频会话。"
        return True, f"已降低 {lowered} 个音频会话的音量。"

    def restore_volume(self):
        try:
            from pycaw.pycaw import AudioUtilities
        except Exception:
            self._reduced_sessions.clear()
            return False, "音量控制依赖不可用，请检查 pycaw 环境。"

        restored = 0
        remaining = {}

        try:
            sessions = AudioUtilities.GetAllSessions()
            for key, original_volume in self._reduced_sessions.items():
                process_name, _, pid_text = key.partition(":")
                matched = False
                for session in sessions:
                    if not session.Process:
                        continue
                    if session.Process.name().lower() != process_name:
                        continue
                    if str(session.Process.pid) != pid_text:
                        continue

                    session.SimpleAudioVolume.SetMasterVolume(original_volume, None)
                    restored += 1
                    matched = True
                    break

                if not matched:
                    remaining[key] = original_volume
        except Exception as e:
            return False, f"恢复游戏音量失败：{e}"

        self._reduced_sessions = remaining
        return True, f"已恢复 {restored} 个音频会话的音量。"

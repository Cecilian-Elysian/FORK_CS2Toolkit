import os
import shutil

class SoundReplacer:
    def __init__(self, steam_path, logger=None):
        self.steam_path = steam_path
        self.logger = logger

    def _log(self, message):
        if self.logger:
            self.logger.info(message)
        else:
            print(message)

    def replace_sound(self, sound_file_path):
        if not self.steam_path:
            return {"success": False, "error": "Steam 路径未提供。"}
        
        try:
            file_name_with_ext = os.path.basename(sound_file_path)
            file_name_no_ext = os.path.splitext(file_name_with_ext)[0]

            # 创建 customsounds 文件夹
            custom_sounds_dir = os.path.join(self.steam_path, "game", "csgo", "customsounds")
            os.makedirs(custom_sounds_dir, exist_ok=True)
            self._log(f"已确认文件夹存在：{custom_sounds_dir}")

            # 复制文件
            destination_path = os.path.join(custom_sounds_dir, file_name_with_ext)
            shutil.copy2(sound_file_path, destination_path)
            self._log(f"已将文件 '{file_name_with_ext}' 复制到 '{destination_path}'")

            # 创建 op.cfg
            cfg_dir = os.path.join(self.steam_path, "game", "csgo", "cfg")
            op_cfg_path = os.path.join(cfg_dir, "op.cfg")
            cfg_content = f"sleep 3\nstopsound\nplay \\customsounds\\{file_name_no_ext}"
            with open(op_cfg_path, "w", encoding='utf-8') as f:
                f.write(cfg_content)
            self._log(f"已创建并写入 op.cfg 文件：{op_cfg_path}")

            # 修改 autoexec.cfg
            autoexec_path = os.path.join(cfg_dir, "autoexec.cfg")
            exec_line = "exec_async op"
            
            lines = []
            if os.path.exists(autoexec_path):
                with open(autoexec_path, "r", encoding='utf-8') as f:
                    lines = f.readlines()
            
            lines = [line for line in lines if "exec_async op" not in line.strip()]
            lines.insert(0, exec_line + "\n")

            with open(autoexec_path, "w", encoding='utf-8') as f:
                f.writelines(lines)

            self._log(f"已成功将 '{exec_line}' 插入到 '{autoexec_path}' 的第一行。")
            return {"success": True, "sound_name": file_name_no_ext}

        except Exception as e:
            self._log(f"替换音效时发生错误：{e}")
            return {"success": False, "error": str(e)}

    def restore_sound(self):
        # 还原启动音效到默认状态
        if not self.steam_path:
            return {"success": False, "error": "Steam 路径未提供。"}
        
        try:
            cfg_dir = os.path.join(self.steam_path, "game", "csgo", "cfg")
            
            # 删除 op.cfg 文件
            op_cfg_path = os.path.join(cfg_dir, "op.cfg")
            if os.path.exists(op_cfg_path):
                os.remove(op_cfg_path)
                self._log(f"已删除 op.cfg 文件：{op_cfg_path}")
            else:
                self._log("op.cfg 文件不存在，无需删除")

            # 从 autoexec.cfg 中移除 exec_async op 命令
            autoexec_path = os.path.join(cfg_dir, "autoexec.cfg")
            if os.path.exists(autoexec_path):
                with open(autoexec_path, "r", encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 移除包含 exec_async op 的行
                original_count = len(lines)
                lines = [line for line in lines if "exec_async op" not in line.strip()]
                removed_count = original_count - len(lines)
                
                with open(autoexec_path, "w", encoding='utf-8') as f:
                    f.writelines(lines)
                
                if removed_count > 0:
                    self._log(f"已从 autoexec.cfg 中移除 {removed_count} 行 exec_async op 命令")
                else:
                    self._log("autoexec.cfg 中未找到 exec_async op 命令")
            else:
                self._log("autoexec.cfg 文件不存在")

            self._log("启动音效已成功还原到默认状态")
            return {"success": True, "message": "启动音效已还原到默认状态"}

        except Exception as e:
            self._log(f"还原音效时发生错误：{e}")
            return {"success": False, "error": str(e)}
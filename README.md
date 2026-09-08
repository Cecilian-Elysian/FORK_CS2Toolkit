# CS2 Death Switch

CS2 Death Switch 是一款 Windows 桌面工具，用于监听《反恐精英 2》（Counter-Strike 2）的游戏状态集成（Game State Integration, GSI）。当本地玩家阵亡时，工具会自动切换到你配置的网页或本地应用；当玩家复活或新回合开始时，会暂停当前 Windows 媒体会话并切回 CS2。

本项目是原 CS2Toolkit 的 Rust 重写版。原有的资源替换、音效事件、视觉叠加、桌宠、预设、更新和自定义等功能已被有意移除。

## 环境要求

- Windows 10 1809 或更高版本
- 反恐精英 2（Counter-Strike 2）
- 从源码构建需要 Rust 1.85 或更高版本

界面为简体中文。应用启动时会自动从系统字体目录（`%WINDIR%\Fonts`）加载 CJK 字体，按顺序尝试微软雅黑（`msyh.ttc`）、黑体、宋体和等线。程序不内置字体文件；如果以上字体均不存在，中文文本可能会显示为方块。

## 构建与运行

```powershell
cargo run --release
```

应用使用独立的新配置目录：

```text
%LOCALAPPDATA%\CS2DeathSwitch\config.json
```

它不会读取、迁移或删除 `%LOCALAPPDATA%\CS2Toolkit` 的数据。

## 打包与发布

编译发行版，得到单文件可执行程序：

```powershell
cargo build --release
```

产物：`target\release\cs2-death-switch.exe`

该程序为独立的单文件发布，无第三方 DLL 依赖（运行库均为 Windows 系统自带，CJK 字体在运行时从系统字体目录加载），解压即可运行。

发布步骤：

1. 将 `cs2-death-switch.exe` 连同 `README.md`、`LICENSE` 一起放入发布目录。
2. 将其压缩为 zip（或直接发布 exe）。
3. 在 GitHub 仓库创建 Release，填写版本号（如 `v0.1.0`）与说明，上传上述文件。

若已安装并登录 [GitHub CLI](https://cli.github.com)，可用 `gh release create` 发布。

## 使用步骤

1. 启动应用。
2. 输入网页 URL 或选择本地应用。
3. 选择或自动检测 CS2 安装目录。
4. 点击「生成 GSI 配置」。
5. 生成配置后重启 CS2。

生成的配置文件位于 CS2 安装目录下的 `game\csgo\cfg\gamestate_integration_cs2deathswitch.cfg`。本地接收端仅绑定 `127.0.0.1`，默认使用端口 `3000`。

## 行为说明

- 首次收到 GSI 更新会建立状态基线，不会触发切换。
- 血量从正数变为 0 时触发一次切换。
- 观战其他玩家时收到的 GSI 更新会被忽略。
- 复活或进入新回合会暂停当前媒体会话，并将 CS2 切回前台。
- 若有延迟切换正在进行中，而此时触发了返回操作，则待定的切换会被取消。
- 在 Windows 提供标准浏览器窗口的情况下，会复用已有的浏览器会话。
- 媒体控制使用当前 Windows 系统媒体会话。Windows 没有可靠的跨浏览器 API 来选择单个标签页。

## 许可证

本项目仍采用 GPL-3.0-only 许可证。详见 [LICENSE](LICENSE)。
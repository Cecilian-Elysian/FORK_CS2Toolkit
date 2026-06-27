# CS2Toolkit - Claude Code (AI 辅助开发) 协同指南

本文档旨在为使用 Claude Code 或其他 AI 编码助手开发 `CS2Toolkit` 项目提供统一的规范、上下文和避坑指南。请在生成代码、重构或调试时，严格遵循以下约定。

## 1. 项目专属配置规范

- **上下文保留策略**：
  - 进行**UI修改**时，必须始终加载 `app/main_window.py` 和 `app/ui/styles.py` 作为上下文。
  - 进行**核心业务逻辑**修改时，必须加载 `app/logic/steam_utils.py`（涉及路径）和 `app/logic/config_manager.py`（涉及预设存储）。
- **权限与文件交互配置**：
  - AI 助手在执行文件读写操作时，需注意区分**项目工作目录**（如 `thumbnails/`、`preconfig.json`）与**Steam/CS2 系统目录**。
  - 测试环境下，禁止 AI 脚本直接向真实 CS2 目录写入超大体积垃圾文件，需优先在沙盒或 Mock 目录验证。

## 2. 代码生成与调试约定

- **技术栈要求**：
  - **核心框架**：严格使用 `PySide6`（**禁用** `PyQt5`、`PyQt6` 或 `PySide2`）。
  - **UI 组件库**：优先使用 `PySide6-Fluent-Widgets` (qfluentwidgets) 提供的现代化组件（如 `InfoBar`, `FluentWindow`, `MessageBox`），少用原生 `QMessageBox`。
- **编码与架构规范**：
  - **UI 与逻辑分离**：`app/ui` 目录下的类只负责界面渲染与事件绑定；实际的 I/O 和计算必须委托给 `app/logic` 下的类。
  - **导入规范**：统一使用绝对导入，例如 `from app.logic.config_manager import ConfigManager`，禁止使用隐式相对导入。
- **禁用的错误实现方案**：
  - **禁用 OpenCV (`cv2`)**：处理视频缩略图时，禁止引入 `cv2`，必须使用现有的 `PySide6.QtMultimedia` 方案（参考 `main_window.py` 中的 `_request_thumbnail`）。
  - **禁用阻塞主线程**：所有耗时操作（如视频复制、GSI 服务器启动、大文件读取）禁止在 UI 线程直接执行。

## 3. 项目结构说明

- `main.py`：应用入口，仅包含初始化 QApplication 和设置 AppUserModelID 的最简逻辑。**（敏感文件，非必要勿动）**
- `app/ui/`：视图层。包含各个功能分页（`video_page.py`, `font_page.py` 等）。
- `app/logic/`：核心业务逻辑。
  - `gsi_manager.py` / `gsi_sound_handler.py`：GSI 本地服务器及事件解析。
  - `steam_utils.py`：Steam 与 CS2 路径检测的核心算法（依赖注册表和 `libraryfolders.vdf`）。**（敏感文件，修改需严谨测试）**
  - `sound_player.py`：基于 `QMediaPlayer` 的并发音效池。
- `app/assets/`：静态资源与图标转码文件（`.py` 格式资源）。

## 4. 开发流程协同规则

- **代码提交前的 Claude Code 检查项**：
  - 检查是否在非主线程（如 GSI 的 HTTP Server 线程）直接调用了 UI 更新方法？如果是，必须改为通过 `Signal.emit()` 派发。
  - 检查路径拼接是否使用了 `os.path.join` 而非硬编码的 `\` 或 `/`，以兼容不同环境。
  - 检查异常捕获是否完整？是否向 UI 抛出了用户友好的 `InfoBar.error` 提示。
- **PR 评审辅助验证**：
  - 验证新增功能是否适配了"暗黑模式"（Dark Mode），`qfluentwidgets` 的样式切换逻辑是否被破坏。
  - 验证 GSI 监听等 Socket 操作在窗口关闭 (`closeEvent`) 时是否正确释放了端口和结束了线程。

## 5. 避坑记录 (Gotchas)

- **坑 1：GSI 端口被占用导致服务崩溃**
  - *场景*：玩家同时运行了其他 GSI 插件占用 3000 端口。
  - *规避方案*：AI 生成 GSI 服务代码时，必须保留并完善端口重试逻辑（`_find_available_port`），并动态生成 `.cfg` 文件映射新端口。
- **坑 2：QMediaPlayer 实例被垃圾回收导致音效中断**
  - *场景*：局部变量创建 `QMediaPlayer` 播放音效，函数执行完毕后对象被销毁，声音戛然而止。
  - *规避方案*：使用或参考 `sound_player.py` 中维护的 `self._players` 实例池，确保播放完成（`EndOfMedia`）前不被 GC。
- **坑 3：跨线程 UI 更新导致程序闪退**
  - *场景*：`HTTPServer` 收到 POST 请求后直接修改 `QLabel.setText()`。
  - *规避方案*：必须使用项目中已定义的 `GsiSignalEmitter` 进行跨线程通信。
- **坑 4：FluentIcon (FIF) 赋值类型错误**
  - *场景*：在使用 `qfluentwidgets` 的图标枚举时（如 `FIF.QUIET_HOURS`），如果将其作为参数传递给 `QPushButton.setIcon()` 等需要实例化 `QIcon` 的 Qt 原生方法，会抛出 `TypeError: 'PySide6.QtWidgets.QAbstractButton.setIcon' called with wrong argument types`。
  - *规避方案*：在原生方法（如 `setIcon`）中必须调用枚举的 `.icon()` 方法将其转为实例，即 `btn.setIcon(FIF.QUIET_HOURS.icon())`。但在使用 Fluent 封装好的组件或方法（如 `addSubInterface`）时，直接传递枚举 `FIF.XXX` 即可。

## 6. Nuitka 编译与构建约定 (极其重要)

本项目使用 Nuitka 将 Python 编译为单文件可执行程序 (`.exe`)。AI 在进行代码生成时，必须时刻考虑编译后的行为差异：
- **依赖与插件更新**：若引入了新的 `PySide6` 模块（例如引入 `QtNetwork`），**必须**同步修改根目录的 `build.py`，添加相应的 `--include-package` 和 `--include-qt-plugins` 指令。否则，编译后的客户端会因缺失底层 DLL 或模块而崩溃。
- **禁用模块黑名单**：`build.py` 中已配置 `--nofollow-import-to`，禁用了 `cv2`, `tkinter`, `pkg_resources` 等库。AI 绝对不可在任何代码中引入这些包。
- **路径与文件系统隔离**：Nuitka 开启 `--onefile` 参数后，程序在运行时会将自身解压到系统的临时目录（Temp）。
  - 读取/写入**用户持久化数据**（如配置文件、预设、缩略图），必须继续使用当前的做法，即依赖 `os.getcwd()` 获取用户实际运行目录。
  - **严禁**尝试将动态生成的文件（如 json、截图）写回 `__file__` 所在的相对目录，因为编译后的执行环境是只读且临时的。
- **动态导入风险**：Nuitka 对隐式导入（如 `importlib.import_module` 或 `__import__`）的静态分析支持较弱。AI 生成的代码必须使用**显式的静态 `import`**。

## 7. 静态资源与版本管理

- **自动主题适配的图标 (FluentIcon)**：本项目使用 `qfluentwidgets.FluentIcon` 替代繁琐的自定义图标管理。严禁手动生成深色/浅色 `.ico` 文件。添加新页面时，直接使用内置枚举（如 `FIF.SETTING`）。
- **Qt 资源系统 (RCC)**：项目中仅保留基础的 UI 图标（如 `app_icon.ico`），如果必须使用自定义图标（非 Fluent 预设），需使用 `pyside6-rcc` 编译为 Python 模块，AI 需使用 `:/xxx.ico` 格式引用，并提醒用户手动运行 rcc 重新编译资源文件，切忌直接通过绝对路径去读取未经编译的图片。
- **版本号同步**：如果完成了新功能的迭代开发并准备打包，AI 应主动检查并同步更新 `main_window.py` 中的 `self.version` 以及后端的 `version.json`（若有权限），以确保更新推送系统的正常运转。

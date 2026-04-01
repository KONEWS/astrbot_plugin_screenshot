📸 AstrBot 完美截图插件（Win11 高分屏适配）

一个基于 Python 实现的 AstrBot 插件，用于在 Windows 系统下进行全屏截图，并解决 Windows 11 高 DPI 缩放导致的截图不完整问题。

✨ 功能特性
🖥 支持 Windows 全屏截图
🔍 适配 Win11 高分屏缩放（DPI）
⚡ 响应快速，指令触发即截图
📦 轻量级实现，无额外复杂依赖
🤖 可直接通过 AstrBot 指令调用
📌 使用方式

发送指令：电脑截图
即可获取当前屏幕截图。
🛠 安装方法
1. 克隆仓库
git clone https://github.com/KONEWS/astrbot_plugin_screenshot.git

2. 放入插件目录
将文件夹放入 AstrBot 插件目录中：
astrbot_plugin_screenshot/
3. 安装依赖
pip install pillow

⚙️ 插件信息
项目	内容
插件名	astrbot_plugin_screenshot
作者	KONEHWS
版本	1.1.0
平台	Windows

⚠️ 注意事项
仅支持 Windows 系统
在远程桌面（RDP）环境下可能截图失败
需保证程序运行在有图形界面的桌面环境
🧠 实现原理

插件基于 PIL.ImageGrab 实现截图，并通过：
ctypes.windll.user32.SetProcessDPIAware()
解决高 DPI 缩放带来的截图偏移问题。

📷 示例
执行指令后，Bot 会返回当前屏幕截图图片。

📄 开源协议

MIT License

❤️ 致谢

感谢 AstrBot 提供插件系统支持。

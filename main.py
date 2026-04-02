import os
import ctypes
import time
import uuid
import platform
import asyncio
from pathlib import Path

# 外部依赖，请确保运行环境已安装 mss 和 Pillow
import mss
from PIL import Image, ImageGrab

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger

@register(
    name="astrbot_plugin_screenshot",
    author="KONEHWS",
    desc="高稳定截图插件",
    version="2.0.5"
)
class PythonScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self._background_tasks = set()

        if platform.system() == "Windows":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
                logger.info("已启用 Per-Monitor DPI Aware")
            except Exception as e:
                logger.warning(f"DPI 设置失败: {e}")

    # ========================
    # 将指令拆分为独立的触发入口，避免被框架覆盖吞噬
    # ========================
    @filter.command("电脑截图")
    async def take_screenshot_base(self, event: AstrMessageEvent):
        async for res in self._core_logic(event): yield res

    @filter.command("电脑截图1")
    async def take_screenshot_1(self, event: AstrMessageEvent):
        async for res in self._core_logic(event): yield res

    @filter.command("电脑截图2")
    async def take_screenshot_2(self, event: AstrMessageEvent):
        async for res in self._core_logic(event): yield res

    @filter.command("电脑截图3")
    async def take_screenshot_3(self, event: AstrMessageEvent):
        async for res in self._core_logic(event): yield res

    @filter.command("电脑截图4")
    async def take_screenshot_4(self, event: AstrMessageEvent):
        async for res in self._core_logic(event): yield res

    # ========================
    # 核心业务逻辑
    # ========================
    async def _core_logic(self, event: AstrMessageEvent):
        if platform.system() != "Windows":
            yield event.plain_result("❌ 当前仅支持 Windows 系统")
            return

        logger.info("收到截图请求")

        try:
            msg_str = event.message_str.strip()
            delay = 0
            monitor_index = 1 # 默认为 1 (主屏)

            # 智能提取指令后方的所有字符 (兼容前缀符号和空格)
            if "电脑截图" in msg_str:
                args_str = msg_str.split("电脑截图", 1)[1].strip()
                args = args_str.split()

                if len(args) == 1:
                    if args[0].isdigit():
                        monitor_index = int(args[0])
                elif len(args) >= 2:
                    if args[0].isdigit():
                        monitor_index = int(args[0])
                    if args[1].isdigit():
                        delay = int(args[1])

            # 延迟截图
            if delay > 0:
                yield event.plain_result(f"⏳ 将在 {delay} 秒后截取屏幕 {monitor_index}...")
                await asyncio.sleep(delay)

            # 获取保存路径
            data_dir = StarTools.get_data_dir()
            data_dir.mkdir(parents=True, exist_ok=True)
            file_name = f"screenshot_{int(time.time())}_{uuid.uuid4().hex}.png"
            save_path = data_dir / file_name

            # 执行截图 (优先 mss)
            try:
                with mss.mss() as sct:
                    monitors = sct.monitors
                    if monitor_index >= len(monitors) or monitor_index < 0:
                        monitor_index = 1 # 超出范围回退到主屏

                    monitor = monitors[monitor_index]
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    logger.info(f"使用 mss 截图（屏幕 {monitor_index}）")
            except Exception as mss_error:
                logger.warning(f"mss 失败，尝试 ImageGrab: {mss_error}")
                img = ImageGrab.grab()

            img.save(save_path)
            yield event.image_result(str(save_path))

            # 安全清理
            task = asyncio.create_task(self._safe_delete(save_path))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        except Exception as e:
            logger.error(f"截图失败: {e}", exc_info=True)
            yield event.plain_result("❌ 截图失败，请查看日志")

    async def _safe_delete(self, path: Path):
        try:
            await asyncio.sleep(8)
            if path.exists():
                path.unlink()
                logger.info(f"已清理截图文件: {path}")
        except Exception as e:
            logger.warning(f"清理文件失败: {e}")
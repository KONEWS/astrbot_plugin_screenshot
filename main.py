import os
import ctypes
import time
import uuid
import platform
from pathlib import Path
from PIL import ImageGrab

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register(
    name="python_screenshot",
    author="KONEHWS",
    desc="适配Win11缩放的全屏截图插件",
    version="1.2.0"
)
class PythonScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("电脑截图")
    async def take_screenshot(self, event: AstrMessageEvent):
        # ✅ 平台限制
        if platform.system() != "Windows":
            yield event.plain_result("❌ 当前仅支持 Windows 系统")
            return

        logger.info("收到截图请求")

        try:
            # ✅ DPI 处理（Win）
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception as e:
                logger.warning(f"DPI 设置失败: {e}")

            # ✅ 使用规范数据目录（兼容无 API 情况）
            data_dir = self.get_data_dir_safe()
            file_name = f"screenshot_{int(time.time())}_{uuid.uuid4().hex}.png"
            save_path = data_dir / file_name

            logger.info(f"截图保存路径: {save_path}")

            # 执行截图
            img = ImageGrab.grab()
            img.save(save_path)

            # 发送图片
            yield event.image_result(str(save_path))

        except Exception as e:
            # ✅ 详细错误写日志，不返回给用户
            logger.error(f"截图失败: {e}", exc_info=True)
            yield event.plain_result("❌ 截图失败，请联系管理员")

    def get_data_dir_safe(self) -> Path:
        """获取插件数据目录（兼容不同 AstrBot 版本）"""
        try:
            # 优先使用官方 API
            return Path(self.context.get_data_dir())
        except Exception:
            # fallback：手动目录
            fallback = Path(os.getcwd()) / "astrbot_plugin_screenshot_data"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
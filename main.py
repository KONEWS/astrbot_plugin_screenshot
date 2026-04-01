import os
import ctypes
import time
import platform
from PIL import ImageGrab

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register(
    name="python_screenshot",
    author="KONEHWS",
    desc="适配Win11缩放的全屏截图插件",
    version="1.1.0"
)
class PythonScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("电脑截图")
    async def take_screenshot(self, event: AstrMessageEvent):
        if platform.system() != "Windows":
            yield event.plain_result("❌ 该插件仅支持 Windows 系统环境。")
            return

        yield event.plain_result("正在截取当前屏幕，请稍候...")
        logger.info("收到截图请求，正在执行...")

        try:
            ctypes.windll.user32.SetProcessDPIAware()

            # ✅ 替换这里（兼容所有版本）
            data_dir = os.path.join(os.getcwd(), "screenshot_cache")
            os.makedirs(data_dir, exist_ok=True)

            file_name = f"screenshot_{int(time.time())}.png"
            save_path = os.path.join(data_dir, file_name)

            img = ImageGrab.grab()
            img.save(save_path)

            logger.info(f"截图已保存至: {save_path}")

            yield event.image_result(save_path)

        except Exception as e:
            logger.error(f"截图插件运行出错: {str(e)}")
            yield event.plain_result("❌ 截图过程中发生错误，请查看日志。")
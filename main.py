import os
import ctypes
import time
import platform
from PIL import ImageGrab
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger # 引入官方规范日志工具

@register("python_screenshot", "知我麻社", "适配Win11缩放的全屏截图插件", "1.1.0")
class PythonScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("电脑截图")
    async def take_screenshot(self, event: AstrMessageEvent):
        # 1. 平台依赖显式约束：判断是否为 Windows
        if platform.system() != "Windows":
            yield event.plain_result("❌ 该插件仅支持 Windows 系统环境。")
            return

        yield event.plain_result("正在截取当前屏幕，请稍候...")
        logger.info("收到截图请求，正在执行...")

        try:
            # 解决高 DPI 缩放问题
            ctypes.windll.user32.SetProcessDPIAware()
            
            # 2. 数据持久化路径规范：获取插件专属数据目录
            # 3. 解决并发冲突：使用时间戳生成唯一文件名
            data_dir = self.context.get_data_dir()
            file_name = f"screenshot_{int(time.time())}.png"
            save_path = os.path.join(data_dir, file_name)
            
            # 执行截图并保存
            img = ImageGrab.grab()
            img.save(save_path)
            
            logger.info(f"截图已保存至: {save_path}")
            
            # 发送图片
            yield event.image_result(save_path)
            
            # 发送完后稍微清理一下，不占用过多空间（可选）
            # os.remove(save_path) 
            
        except Exception as e:
            # 4. 异常信息脱敏：不把具体代码错误发给用户，但记入日志
            logger.error(f"截图插件运行出错: {str(e)}")
            yield event.plain_result("❌ 截图过程中发生未知错误，请联系管理员查看日志。")
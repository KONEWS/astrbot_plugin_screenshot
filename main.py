import os
import ctypes
from PIL import ImageGrab
# 【核心修复】不使用星号模糊导入，而是精准指定我们需要 AstrBot 的 filter 和事件工具
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("python_screenshot", "知我麻社", "使用Python原生截图，解决Win11缩放截不全问题", "1.0.0")
class PythonScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 自定义的触发词
    @filter.command("电脑截图")
    async def take_screenshot(self, event: AstrMessageEvent):
        # 先回复一句提示，让用户知道机器人在干活
        yield event.plain_result("正在截取当前屏幕，请稍候...")
        
        try:
            # 调用系统底层接口，强制适配高 DPI 缩放，防止画面被裁剪
            ctypes.windll.user32.SetProcessDPIAware()
            
            # 定义图片保存的路径
            save_path = os.path.join(os.getcwd(), "screenshot.png")
            
            # 执行全屏截图动作
            img = ImageGrab.grab()
            
            # 把截好的图片保存到电脑硬盘上
            img.save(save_path)
            
            # 把保存好的图片发送到聊天软件中
            yield event.image_result(save_path)
            
        except Exception as e:
            # 如果发生任何意外错误，把具体的错误原因发出来，方便排查
            yield event.plain_result(f"截图失败了，错误详情：{str(e)}")
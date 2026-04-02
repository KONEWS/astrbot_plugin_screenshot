import os
import ctypes
import time
import uuid
import base64
import platform
import asyncio
import re
from pathlib import Path

import mss
from PIL import Image

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger


@register("astrbot_plugin_screenshot", "KONEHWS", "稳定截图插件", "1.2.2")
class PythonScreenshotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self._background_tasks: set = set()

    async def initialize(self):
        """插件初始化：确认运行环境并配置 DPI 感知。"""
        if platform.system() != "Windows":
            logger.warning("astrbot_plugin_screenshot: 当前系统非 Windows，截图功能不可用")
            return

        # 必须在 mss 首次 grab 之前设置，确保高 DPI / 125%~150% 缩放屏幕截图完整
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            logger.info("astrbot_plugin_screenshot: 已启用 Per-Monitor DPI Aware，高分屏截图完整")
        except Exception as e:
            logger.warning(f"DPI 设置失败（可能已由框架设置过）: {e}")

        logger.info("astrbot_plugin_screenshot: 初始化成功，运行于 Windows 环境")

    # ========================
    # 指令入口
    # ========================
    @filter.command("电脑截图")
    async def take_screenshot(self, event: AstrMessageEvent):
        """截取主屏幕，发送图片并让 AI 分析内容。可选：延迟秒数、自定义分析提示词。"""
        if platform.system() != "Windows":
            yield event.plain_result("❌ 当前仅支持 Windows 系统")
            return

        logger.info("收到截图请求")

        delay, prompt = self._parse_args(event.message_str.strip())

        if delay > 0:
            yield event.plain_result(f"⏳ 将在 {delay} 秒后截取屏幕...")
            await asyncio.sleep(delay)

        # 执行截图
        try:
            # ✅ 修改 4：使用 to_thread 将耗时的同步 I/O 操作扔给线程池，防止阻塞事件循环
            save_path = await asyncio.to_thread(self._capture_and_save)
        except RuntimeError as e:
            yield event.plain_result(str(e))
            return
        except Exception as e:
            logger.error(f"截图异常: {e}", exc_info=True)
            yield event.plain_result("❌ 截图失败，请查看日志")
            return

        # 先发送截图
        yield event.image_result(str(save_path))
        logger.info(f"截图已发送: {save_path}")

        # AI 分析
        yield event.plain_result("🤖 正在分析截图，请稍候...")
        try:
            analysis = await self._analyze(save_path, prompt)
            yield event.plain_result(analysis)
        except Exception as e:
            logger.error(f"AI 分析失败: {e}", exc_info=True)
            yield event.plain_result("❌ AI 分析发生错误，请查看日志")

        self._schedule_cleanup(save_path, delay_seconds=30)

    # ========================
    # 参数解析
    # ========================
    @staticmethod
    def _parse_args(msg_str: str) -> tuple[int, str]:
        default_prompt = "请详细描述这张屏幕截图的内容，包括正在运行的程序、显示的文字和界面布局。"
        rest = re.sub(r"^.*?电脑截图\s*", "", msg_str).strip()
        if not rest:
            return 0, default_prompt
        parts = rest.split(None, 1)
        if parts[0].isdigit():
            # ✅ 修改 1：增加延迟上限限制，防止恶意输入导致协程无限挂起
            delay = min(int(parts[0]), 60)
            prompt = parts[1].strip() if len(parts) > 1 else default_prompt
        else:
            delay = 0
            prompt = rest
        return delay, prompt

    # ========================
    # 截图并保存，返回保存路径
    # ========================
    @staticmethod
    def _capture_and_save() -> Path:
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                logger.info(f"截图成功，尺寸: {img.size}")
        except Exception as e:
            logger.error(f"截图失败: {e}", exc_info=True)
            raise RuntimeError("❌ 截图失败，请查看物理显示器是否正常工作") from e

        data_dir = StarTools.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"screenshot_{int(time.time())}_{uuid.uuid4().hex}.png"
        save_path = data_dir / file_name
        img.save(save_path)
        return save_path

    # ========================
    # 调用 AstrBot 内置 LLM 分析截图
    # ========================
    async def _analyze(self, image_path: Path, prompt: str) -> str:
        # ✅ 修改 3：缺失 LLM 供应商的判空保护
        provider = self.context.get_using_provider()
        if not provider:
            return "❌ 尚未配置或启用任何大模型供应商，无法进行图片分析。"

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        response = await provider.text_chat(
            prompt=prompt,
            image_urls=[f"data:image/png;base64,{image_b64}"]
        )
        return response.completion_text

    # ========================
    # 后台延迟清理临时截图文件
    # ========================
    def _schedule_cleanup(self, path: Path, delay_seconds: int = 30):
        if len(self._background_tasks) > 50:
            logger.warning("后台清理任务数量超过 50，可能存在任务堆积")
        task = asyncio.create_task(self._safe_delete(path, delay_seconds))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _safe_delete(self, path: Path, delay_seconds: int):
        # ✅ 修改 2：将文件删除逻辑移入 finally 块，防止任务被强杀时发生资源泄漏
        try:
            await asyncio.sleep(delay_seconds)
        finally:
            if path.exists():
                try:
                    path.unlink()
                    logger.info(f"已安全清理截图文件: {path}")
                except Exception as e:
                    logger.warning(f"文件删除失败，可能被占用: {e}")

    async def terminate(self):
        """插件销毁：取消所有未完成的后台清理任务。"""
        for task in list(self._background_tasks):
            task.cancel()
        self._background_tasks.clear()
        logger.info("astrbot_plugin_screenshot: 已安全销毁，后台任务已清空")

"""
浏览器管理器 - 用于控制和监控 Streamlit 应用
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime


class BrowserManager:
    """管理浏览器和 Streamlit 应用"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.streamlit_process = None
        self.browser = None
        self.page = None
        self.console_logs = []
        self.network_logs = []
        self.errors = []
        self.screenshots_dir = Path(project_root) / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Playwright 相关
        self.playwright = None
        self.browser_context = None
    
    async def start_streamlit(self, port: int = 8501) -> bool:
        """启动 Streamlit 应用"""
        try:
            # 检查是否已经在运行
            if self.streamlit_process and self.streamlit_process.poll() is None:
                return True
            
            # 启动 Streamlit
            app_path = os.path.join(self.project_root, "app.py")
            self.streamlit_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", app_path, 
                 "--server.port", str(port),
                 "--server.headless", "true"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )
            
            # 等待启动
            await asyncio.sleep(5)
            return True
        except Exception as e:
            print(f"启动 Streamlit 失败: {e}")
            return False
    
    async def start_browser(self, url: str = "http://localhost:8501") -> bool:
        """启动浏览器并连接到应用"""
        try:
            from playwright.async_api import async_playwright
            
            if not self.playwright:
                self.playwright = await async_playwright().start()
            
            if not self.browser:
                # 尝试使用系统的 Edge 浏览器（Windows 自带）
                try:
                    self.browser = await self.playwright.chromium.launch(
                        channel="msedge",  # 使用 Edge
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                except Exception as e:
                    print(f"使用 Edge 失败，尝试 Chromium: {e}")
                    # 如果 Edge 失败，尝试 Chromium
                    self.browser = await self.playwright.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
            
            if not self.browser_context:
                self.browser_context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
            
            if not self.page:
                self.page = await self.browser_context.new_page()
                
                # 监听控制台
                self.page.on("console", self._on_console)
                
                # 监听错误
                self.page.on("pageerror", self._on_page_error)
                
                # 监听网络请求
                self.page.on("request", self._on_request)
                self.page.on("response", self._on_response)
            
            # 访问应用
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)  # 等待 Streamlit 完全加载
            
            return True
        except Exception as e:
            print(f"启动浏览器失败: {e}")
            return False
    
    def _on_console(self, msg):
        """控制台消息回调"""
        log_entry = {
            "type": msg.type,
            "text": msg.text,
            "timestamp": datetime.now().isoformat()
        }
        self.console_logs.append(log_entry)
        
        # 只保留最近 100 条
        if len(self.console_logs) > 100:
            self.console_logs = self.console_logs[-100:]
    
    def _on_page_error(self, error):
        """页面错误回调"""
        error_entry = {
            "message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        self.errors.append(error_entry)
        
        # 只保留最近 50 条
        if len(self.errors) > 50:
            self.errors = self.errors[-50:]
    
    def _on_request(self, request):
        """网络请求回调"""
        log_entry = {
            "type": "request",
            "url": request.url,
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        }
        self.network_logs.append(log_entry)
    
    def _on_response(self, response):
        """网络响应回调"""
        log_entry = {
            "type": "response",
            "url": response.url,
            "status": response.status,
            "timestamp": datetime.now().isoformat()
        }
        self.network_logs.append(log_entry)
        
        # 只保留最近 100 条
        if len(self.network_logs) > 100:
            self.network_logs = self.network_logs[-100:]
    
    async def screenshot(self, filename: Optional[str] = None) -> str:
        """截图并返回路径"""
        if not self.page:
            raise Exception("浏览器未启动")
        
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = self.screenshots_dir / filename
        await self.page.screenshot(path=str(filepath), full_page=True)
        return str(filepath)
    
    async def get_screenshot_base64(self) -> str:
        """获取截图的 base64 编码"""
        filepath = await self.screenshot()
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def get_console_logs(self, last_n: int = 20) -> List[Dict]:
        """获取最近的控制台日志"""
        return self.console_logs[-last_n:]
    
    def get_errors(self, last_n: int = 10) -> List[Dict]:
        """获取最近的错误"""
        return self.errors[-last_n:]
    
    def get_network_logs(self, last_n: int = 20) -> List[Dict]:
        """获取最近的网络日志"""
        return self.network_logs[-last_n:]
    
    async def click_element(self, selector: str) -> bool:
        """点击元素"""
        if not self.page:
            raise Exception("浏览器未启动")
        
        try:
            await self.page.click(selector, timeout=5000)
            return True
        except Exception as e:
            print(f"点击元素失败: {e}")
            return False
    
    async def get_element_info(self, selector: str) -> Optional[Dict]:
        """获取元素信息"""
        if not self.page:
            raise Exception("浏览器未启动")
        
        try:
            element = await self.page.query_selector(selector)
            if not element:
                return None
            
            box = await element.bounding_box()
            text = await element.text_content()
            
            return {
                "selector": selector,
                "text": text,
                "position": box,
                "visible": await element.is_visible()
            }
        except Exception as e:
            print(f"获取元素信息失败: {e}")
            return None
    
    async def execute_javascript(self, code: str) -> Any:
        """执行 JavaScript 代码"""
        if not self.page:
            raise Exception("浏览器未启动")
        
        try:
            result = await self.page.evaluate(code)
            return result
        except Exception as e:
            print(f"执行 JavaScript 失败: {e}")
            return None
    
    async def get_streamlit_state(self) -> Optional[Dict]:
        """获取 Streamlit session state"""
        # Streamlit 的 session state 在前端不直接可见
        # 但我们可以通过检查 DOM 来推断状态
        try:
            # 检查是否有错误提示
            error_elements = await self.page.query_selector_all(".stException")
            errors = []
            for elem in error_elements:
                text = await elem.text_content()
                errors.append(text)
            
            # 检查是否有警告
            warning_elements = await self.page.query_selector_all(".stWarning")
            warnings = []
            for elem in warning_elements:
                text = await elem.text_content()
                warnings.append(text)
            
            # 检查是否有成功消息
            success_elements = await self.page.query_selector_all(".stSuccess")
            successes = []
            for elem in success_elements:
                text = await elem.text_content()
                successes.append(text)
            
            return {
                "errors": errors,
                "warnings": warnings,
                "successes": successes,
                "url": self.page.url
            }
        except Exception as e:
            print(f"获取 Streamlit 状态失败: {e}")
            return None
    
    async def wait_for_element(self, selector: str, timeout: int = 5000) -> bool:
        """等待元素出现"""
        if not self.page:
            raise Exception("浏览器未启动")
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    async def close(self):
        """关闭浏览器和 Streamlit"""
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        if self.streamlit_process:
            self.streamlit_process.terminate()
            self.streamlit_process.wait(timeout=5)
            self.streamlit_process = None
    
    def clear_logs(self):
        """清空日志"""
        self.console_logs = []
        self.network_logs = []
        self.errors = []

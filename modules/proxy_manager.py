import random
import time
from typing import List, Dict
import requests
from config import Config


class ProxyManager:
    def __init__(self, proxy_file: str = None):
        self.proxy_file = proxy_file or Config.PROXY_FILE
        self.proxies = self.load_proxies()
        self.current_index = 0

    def load_proxies(self) -> List[str]:
        """从文件加载代理IP"""
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies
        except FileNotFoundError:
            print(f"代理文件 {self.proxy_file} 不存在，使用空代理列表")
            return []

    def get_available_proxy(self) -> str:
        """获取可用的代理IP"""
        if not self.proxies:
            return None
        
        # 简单轮询算法，可扩展为根据代理质量选择
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        return proxy

    def validate_proxy(self, proxy: str) -> bool:
        """验证代理是否可用"""
        proxies = {
            'http': f'http://{proxy}',
            'https': f'https://{proxy}'
        }
        
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

    def rotate_proxy(self):
        """轮换代理IP"""
        if self.proxies:
            self.proxies = self.proxies[1:] + [self.proxies[0]]

    def add_proxy(self, proxy: str):
        """添加新的代理IP"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)

    def remove_proxy(self, proxy: str):
        """移除代理IP"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)

    def get_all_proxies(self) -> List[str]:
        """获取所有代理IP"""
        return self.proxies.copy()

    def get_proxy_count(self) -> int:
        """获取代理总数"""
        return len(self.proxies)
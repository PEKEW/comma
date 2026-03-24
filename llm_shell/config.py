"""配置管理模块"""
import json
import os
from pathlib import Path


class Config:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        "api_key": "",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
        "editor": os.environ.get("EDITOR", "vim"),
        "max_history": 20,
        "auto_confirm": False,
        "timeout": 30
    }
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "llm-shell"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    merged = self.DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged
            except (json.JSONDecodeError, IOError):
                pass
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """保存配置到文件"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save()
    
    def is_configured(self):
        """检查是否已配置API Key"""
        return bool(self.get("api_key"))

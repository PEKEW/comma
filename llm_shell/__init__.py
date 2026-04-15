"""LLM Shell - 智能Shell助手"""

__version__ = "0.1.0"
__author__ = "LLM Shell"

from .config import Config
from .llm_client import LLMClient

__all__ = ['main', 'generate_command', 'fix_command', 'Config', 'LLMClient']


def __getattr__(name):
    if name in {"main", "generate_command", "fix_command"}:
        from .main import main, generate_command, fix_command
        exports = {
            "main": main,
            "generate_command": generate_command,
            "fix_command": fix_command,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""LLM Shell - 智能Shell助手"""

__version__ = "0.1.0"
__author__ = "LLM Shell"

from .main import main, generate_command, fix_command
from .config import Config
from .llm_client import LLMClient

__all__ = ['main', 'generate_command', 'fix_command', 'Config', 'LLMClient']

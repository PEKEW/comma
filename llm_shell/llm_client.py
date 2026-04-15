"""LLM API客户端模块"""
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Optional, List, Dict


class LLMClient:
    """LLM API客户端"""
    
    def __init__(self, config, debug: bool = False):
        self.config = config
        self.api_key = config.get("api_key")
        self.api_base = config.get("api_base", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.timeout = config.get("timeout", 30)
        self.debug = debug

    def _debug_log(self, title: str, payload=None) -> None:
        """输出调试日志到 stderr。"""
        if not self.debug:
            return
        print(f"[llm-shell debug] {title}", file=sys.stderr)
        if payload is None:
            return
        if isinstance(payload, (dict, list)):
            text = json.dumps(payload, ensure_ascii=False, indent=2)
        else:
            text = str(payload)
        print(text, file=sys.stderr)

    def _redact_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """脱敏敏感请求头。"""
        redacted = dict(headers)
        for key in ("Authorization", "x-api-key"):
            if key in redacted:
                value = redacted[key]
                if len(value) > 12:
                    redacted[key] = f"{value[:8]}...{value[-4:]}"
                else:
                    redacted[key] = "***"
        return redacted

    def _is_anthropic_format(self) -> bool:
        """检测是否使用 Anthropic 格式（kimi.com/coding 或 anthropic.com）"""
        base = self.api_base.lower()
        return "kimi.com/coding" in base or "anthropic.com" in base

    def _build_request_url(self, base: str) -> str:
        """根据 provider 和 api_base 生成正确的请求 URL。"""
        if self._is_anthropic_format():
            normalized = base.removesuffix("/")
            if normalized.endswith("/v1"):
                return f"{normalized}/messages"
            return f"{normalized}/v1/messages"
        return f"{base}/chat/completions"

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> Optional[str]:
        """
        发送聊天请求到LLM API，自动检测 OpenAI 或 Anthropic 格式

        Returns:
            LLM的回复内容，如果失败则返回None
        """
        if not self.api_key:
            print("\033[91m错误: 未配置API Key，请运行 'llm-shell --config' 进行配置\033[0m", file=sys.stderr)
            return None

        base = self.api_base.rstrip('/')

        if self._is_anthropic_format():
            # Anthropic 格式: POST /v1/messages, x-api-key header
            # 同时兼容 api_base 配成根路径或已带 /v1 的情况
            url = self._build_request_url(base)
            data = {
                "model": self.model,
                "max_tokens": 500,
                "messages": messages,
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
        else:
            # OpenAI 格式: POST /chat/completions, Authorization: Bearer header
            url = self._build_request_url(base)
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 500,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

        try:
            self._debug_log("request url", url)
            self._debug_log("request headers", self._redact_headers(headers))
            self._debug_log("request body", data)
            req = Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urlopen(req, timeout=self.timeout) as response:
                status = getattr(response, "status", None)
                raw_body = response.read().decode('utf-8')
                self._debug_log("response status", status)
                self._debug_log("response body", raw_body)
                result = json.loads(raw_body)
                if self._is_anthropic_format():
                    return result['content'][0]['text'].strip()
                else:
                    return result['choices'][0]['message']['content'].strip()

        except HTTPError as e:
            raw_body = e.read().decode('utf-8', errors='replace')
            self._debug_log("http error", {"code": e.code, "reason": str(e.reason)})
            self._debug_log("http error body", raw_body)
            print(f"\033[91mAPI请求失败: HTTP {e.code} {e.reason}\033[0m", file=sys.stderr)
            return None
        except URLError as e:
            self._debug_log("url error", repr(e))
            print(f"\033[91mAPI请求失败: {e}\033[0m", file=sys.stderr)
            return None
        except json.JSONDecodeError as e:
            self._debug_log("json decode error", repr(e))
            print(f"\033[91m解析响应失败: {e}\033[0m", file=sys.stderr)
            return None
        except Exception as e:
            self._debug_log("unexpected error", repr(e))
            print(f"\033[91m错误: {e}\033[0m", file=sys.stderr)
            return None
    
    def natural_to_command(self, description: str, shell: str = "bash") -> Optional[str]:
        """
        将自然语言描述转换为shell命令
        
        Args:
            description: 自然语言描述
            shell: 当前shell类型
            
        Returns:
            转换后的shell命令
        """
        system_prompt = f"""你是一个shell命令专家。将用户的自然语言描述转换为精确的{shell}命令。
规则:
1. 只输出命令本身，不要有解释、注释或代码块标记
2. 如果存在多个等效命令，选择最常用/标准的那个
3. 如果描述不明确，选择最可能的解释
4. 不要包含危险命令（如rm -rf /）
5. 输出必须是单行命令，除非逻辑上需要多行（此时使用 && 或 ; 连接）
6. 如果用户描述的是"列出当前目录"，优先使用tree（如果可用），否则使用ls -la"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description}
        ]
        
        result = self.chat(messages)
        if result:
            # 清理输出，移除代码块标记
            result = result.strip()
            if result.startswith('```'):
                lines = result.split('\n')
                # 移除开头的 ```bash 或 ```
                if lines[0].startswith('```'):
                    lines = lines[1:]
                # 移除结尾的 ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                result = '\n'.join(lines).strip()
        
        return result
    
    def fix_command(self, command: str, error_output: str, shell: str = "bash") -> Optional[str]:
        """
        根据错误输出修复命令
        
        Args:
            command: 原始命令
            error_output: 错误输出
            shell: 当前shell类型
            
        Returns:
            修复后的命令
        """
        system_prompt = f"""你是一个shell命令修复专家。分析用户的命令和错误输出，提供修复后的正确命令。
规则:
1. 只输出修复后的命令本身，不要有解释、注释或代码块标记
2. 修正typo、语法错误、参数错误等
3. 如果命令不存在，建议使用可用的替代命令
4. 输出必须是可执行的命令
5. 如果无法修复，输出\"无法修复: [原因]\""""

        user_prompt = f"原始命令: {command}\n错误输出:\n{error_output}\n\n请提供修复后的命令:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self.chat(messages)
        if result:
            result = result.strip()
            if result.startswith('```'):
                lines = result.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                result = '\n'.join(lines).strip()
        
        return result
    
    def suggest_from_history(self, history: List[str], shell: str = "bash") -> Optional[str]:
        """
        根据历史记录建议可能的意图
        
        Args:
            history: 命令历史列表
            shell: 当前shell类型
            
        Returns:
            建议的命令
        """
        system_prompt = f"""你是一个shell命令助手。分析用户的命令历史，判断用户是否想要修正或重复之前的某个命令。
规则:
1. 如果历史记录显示用户可能有typo或命令失败，建议修正后的命令
2. 如果用户可能在尝试重复或修改之前的命令，建议最合适的命令
3. 只输出建议的命令本身，不要有解释
4. 如果看不出明确意图，输出"none"
5. 输出必须是可执行的命令"""

        history_text = '\n'.join([f"{i+1}. {cmd}" for i, cmd in enumerate(history[-10:])])
        user_prompt = f"最近的命令历史:\n{history_text}\n\n基于历史，建议一个用户可能想要执行的命令（如果没有明确意图请回复'none'）:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self.chat(messages)
        if result and result.strip().lower() != 'none':
            result = result.strip()
            if result.startswith('```'):
                lines = result.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                result = '\n'.join(lines).strip()
            return result
        return None

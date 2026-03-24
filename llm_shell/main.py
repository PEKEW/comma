#!/usr/bin/env python3
"""
LLM Shell - 智能Shell助手 (无痕集成版)

使用方式:
  1. 在 .zshrc 中: source /path/to/llm-shell.zsh
  2. 在 .bashrc 中: source /path/to/llm-shell.bash
  
然后在shell中:
  | <自然语言描述>  - 将自然语言转换为shell命令并执行
  || <自然语言>    - 将自然语言转换为命令，打开编辑器编辑后执行
  fuck            - 尝试修复上一条失败的命令
  <普通命令>      - 直接执行，不经过LLM
"""

import sys
import os
import argparse
from typing import Optional

from .config import Config
from .llm_client import LLMClient
from .utils import get_shell_type, is_dangerous_command


def generate_command(description: str, shell: str = None) -> Optional[str]:
    """生成命令（供shell脚本调用）"""
    if shell is None:
        shell = get_shell_type()
    
    config = Config()
    llm = LLMClient(config)
    
    return llm.natural_to_command(description, shell)


def fix_command(command: str, shell: str = None) -> Optional[str]:
    """修复命令（供shell脚本调用）"""
    if shell is None:
        shell = get_shell_type()
    
    config = Config()
    llm = LLMClient(config)
    
    # 模拟执行获取错误
    import subprocess
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        error_output = result.stderr if result.stderr else f"exit code: {result.returncode}"
    except Exception as e:
        error_output = str(e)
    
    return llm.fix_command(command, error_output, shell)


def interactive_mode():
    """交互式模式（用于测试或独立使用）"""
    config = Config()
    llm = LLMClient(config)
    shell = get_shell_type()
    
    if not config.is_configured():
        print("\033[91m错误: 未配置API Key\033[0m")
        print("运行: llm-shell --config")
        sys.exit(1)
    
    print("\033[32mLLM Shell 交互模式\033[0m")
    print("提示: | <描述> = 转换, || <描述> = 编辑, exit = 退出")
    print()
    
    while True:
        try:
            user_input = input("\033[36m❯\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ('exit', 'quit', 'q'):
            break
        
        if user_input == '--config':
            setup_config()
            continue
        
        # 处理 ||
        if user_input.startswith('||'):
            description = user_input[2:].strip()
            if not description:
                print("\033[33m用法: || <描述>\033[0m")
                continue
            
            print("\033[2m🤔 思考中...\033[0m")
            cmd = llm.natural_to_command(description, shell)
            if not cmd:
                print("\033[91m无法生成命令\033[0m")
                continue
            
            print(f"\033[36m➜ {cmd}\033[0m")
            
            # 编辑
            from .utils import open_editor
            edited = open_editor(cmd, config.get("editor"))
            edited = edited.strip()
            
            if not edited:
                print("\033[33m已取消\033[0m")
                continue
            
            print(f"\033[36m✎ {edited}\033[0m")
            
            if is_dangerous_command(edited):
                print("\033[91m⚠️ 危险命令！\033[0m")
                confirm = input("确定执行? [y/N] ").strip().lower()
                if confirm not in ('y', 'yes'):
                    continue
            
            os.system(edited)
            continue
        
        # 处理 |
        if user_input.startswith('|'):
            description = user_input[1:].strip()
            if not description:
                print("\033[33m用法: | <描述>\033[0m")
                continue
            
            print("\033[2m🤔 思考中...\033[0m")
            cmd = llm.natural_to_command(description, shell)
            if not cmd:
                print("\033[91m无法生成命令\033[0m")
                continue
            
            print(f"\033[36m➜ {cmd}\033[0m")
            
            response = input("执行? [Y/n/e(编辑)] ").strip().lower()
            
            if response in ('n', 'no'):
                print("\033[33m已取消\033[0m")
                continue
            
            if response in ('e', 'edit'):
                from .utils import open_editor
                edited = open_editor(cmd, config.get("editor"))
                cmd = edited.strip()
                if not cmd:
                    print("\033[33m已取消\033[0m")
                    continue
                print(f"\033[36m➜ {cmd}\033[0m")
            
            if is_dangerous_command(cmd):
                print("\033[91m⚠️ 危险命令！\033[0m")
                confirm = input("确定执行? [y/N] ").strip().lower()
                if confirm not in ('y', 'yes'):
                    continue
            
            os.system(cmd)
            continue
        
        # 普通命令
        exit_code = os.system(user_input)
        if exit_code != 0:
            print(f"\033[33m命令失败 (exit {exit_code})\033[0m")


def setup_config():
    """配置向导"""
    config = Config()
    
    print("\033[1m=== LLM Shell 配置 ===\033[0m")
    
    current_key = config.get("api_key", "")
    masked = "*" * len(current_key) if current_key else "未设置"
    new_key = input(f"API Key [{masked}]: ").strip()
    if new_key:
        config.set("api_key", new_key)
    
    current_base = config.get("api_base")
    new_base = input(f"API Base [{current_base}]: ").strip()
    if new_base:
        config.set("api_base", new_base)
    
    current_model = config.get("model")
    new_model = input(f"Model [{current_model}]: ").strip()
    if new_model:
        config.set("model", new_model)
    
    current_editor = config.get("editor")
    new_editor = input(f"Editor [{current_editor}]: ").strip()
    if new_editor:
        config.set("editor", new_editor)
    
    print("\033[32m✓ 配置已保存!\033[0m")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='LLM Shell - 智能Shell助手',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用方式:
  方式1 - Shell集成（推荐）:
    source shell_integration/llm-shell.zsh  # zsh用户
    source shell_integration/llm-shell.bash # bash用户
    
  方式2 - 交互模式:
    llm-shell
    
  方式3 - 单条命令:
    llm-shell --generate "列出当前目录"
    llm-shell --fix "gi tstatus"
        """
    )
    
    parser.add_argument(
        '--generate', '-g',
        metavar='DESCRIPTION',
        help='根据描述生成命令（用于shell集成）'
    )
    parser.add_argument(
        '--fix', '-f',
        metavar='COMMAND',
        help='修复命令（用于shell集成）'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='配置设置'
    )
    parser.add_argument(
        '--shell',
        default=None,
        help='指定shell类型 (bash/zsh)'
    )
    
    args = parser.parse_args()
    
    if args.config:
        setup_config()
    elif args.generate:
        cmd = generate_command(args.generate, args.shell)
        if cmd:
            print(cmd)
        else:
            sys.exit(1)
    elif args.fix:
        fixed = fix_command(args.fix, args.shell)
        if fixed:
            print(fixed)
        else:
            sys.exit(1)
    else:
        interactive_mode()


if __name__ == '__main__':
    main()

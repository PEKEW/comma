"""工具函数模块"""
import os
import subprocess
import tempfile
from typing import List, Tuple, Optional


def get_shell_type() -> str:
    """获取当前shell类型"""
    shell = os.environ.get('SHELL', '/bin/bash')
    return os.path.basename(shell)


def get_shell_history(max_lines: int = 20) -> List[str]:
    """获取shell历史记录"""
    shell = get_shell_type()
    history = []
    
    try:
        if shell == 'zsh':
            histfile = os.environ.get('HISTFILE', os.path.expanduser('~/.zsh_history'))
            if os.path.exists(histfile):
                with open(histfile, 'r', errors='ignore') as f:
                    lines = f.readlines()
                    # zsh历史格式: : 1234567890:0;command
                    for line in lines[-max_lines:]:
                        if ';' in line:
                            cmd = line.split(';', 1)[1].strip()
                            if cmd:
                                history.append(cmd)
                        else:
                            history.append(line.strip())
        elif shell == 'bash':
            histfile = os.environ.get('HISTFILE', os.path.expanduser('~/.bash_history'))
            if os.path.exists(histfile):
                with open(histfile, 'r') as f:
                    lines = f.readlines()
                    history = [line.strip() for line in lines[-max_lines:] if line.strip()]
        elif shell == 'fish':
            try:
                result = subprocess.run(
                    ['fish', '-c', 'history'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    history = result.stdout.strip().split('\n')[-max_lines:]
            except:
                pass
    except Exception:
        pass
    
    return history


def execute_command(command: str, shell: str = None) -> Tuple[int, str, str]:
    """
    执行shell命令
    
    Returns:
        (returncode, stdout, stderr)
    """
    if shell is None:
        shell = get_shell_type()
    
    try:
        # 使用用户的shell来执行命令
        shell_path = os.environ.get('SHELL', '/bin/bash')
        result = subprocess.run(
            [shell_path, '-c', command],
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except Exception as e:
        return -1, "", str(e)


def open_editor(content: str, editor: str = None) -> str:
    """
    打开编辑器编辑内容
    
    Args:
        content: 初始内容
        editor: 编辑器程序名
        
    Returns:
        编辑后的内容
    """
    if editor is None:
        editor = os.environ.get('EDITOR', 'vim')
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.sh', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # 打开编辑器
        subprocess.run([editor, temp_path], check=True)
        
        # 读取编辑后的内容
        with open(temp_path, 'r') as f:
            return f.read()
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_path)
        except:
            pass


def print_colored(text: str, color: str = 'green'):
    """打印彩色文本"""
    colors = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m'
    }
    
    color_code = colors.get(color, colors['reset'])
    reset_code = colors['reset']
    print(f"{color_code}{text}{reset_code}")


def confirm(prompt: str, default: bool = False) -> bool:
    """
    询问用户确认
    
    Args:
        prompt: 提示信息
        default: 默认选项（True为是，False为否）
        
    Returns:
        用户是否确认
    """
    suffix = " [Y/n] " if default else " [y/N] "
    response = input(prompt + suffix).strip().lower()
    
    if not response:
        return default
    
    return response in ('y', 'yes')


def is_dangerous_command(command: str) -> bool:
    """检查命令是否可能危险"""
    dangerous_patterns = [
        'rm -rf /',
        'rm -rf /*',
        ':(){ :|:& };:',  # fork bomb
        '> /dev/sda',
        'dd if=/dev/zero of=/dev/sda',
        'mkfs.ext4 /dev/sda',
        'mv /* /dev/null',
        'wget', '|', 'bash',  # 管道到bash可能危险，需要警告
        'curl', '|', 'sh',
    ]
    
    cmd_lower = command.lower()
    
    # 检查明显的危险模式
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            return True
    
    # 检查rm -rf （除特定安全目录外）
    if 'rm -rf' in cmd_lower:
        # 如果目标是 / 或空，认为是危险的
        parts = cmd_lower.split('rm -rf')
        if len(parts) > 1:
            target = parts[1].strip().split()[0] if parts[1].strip() else ''
            if target in ('/', '', '$HOME', '~') or target.startswith('/'):
                return True
    
    return False


def format_command_for_display(command: str, max_length: int = 80) -> str:
    """格式化命令以便显示"""
    if len(command) <= max_length:
        return command
    return command[:max_length-3] + '...'

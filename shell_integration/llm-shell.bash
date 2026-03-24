#!/bin/bash
# llm-shell-simple.bash - Bash简单可靠集成
# 使用方法: 在 ~/.bashrc 中添加: source /path/to/llm-shell-simple.bash

# 配置
export LLM_SHELL_DIR="${LLM_SHELL_DIR:-$HOME/.config/llm-shell}"
export LLM_SHELL_CONFIG="${LLM_SHELL_CONFIG:-$LLM_SHELL_DIR/config.json}"
export LLM_SHELL_PYTHON="${LLM_SHELL_PYTHON:-python3}"

# 颜色
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
RESET='\033[0m'

# 检测后端
_llm_shell_detect() {
    if [[ -z "$LLM_SHELL_BACKEND" ]]; then
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [[ -f "$script_dir/../llm_shell/main.py" ]]; then
            export LLM_SHELL_BACKEND="$script_dir/../llm_shell/main.py"
        elif command -v llm-shell &>/dev/null; then
            export LLM_SHELL_BACKEND="llm-shell"
        fi
    fi
}

# 生成命令
_llm_shell_gen() {
    local desc="$1"
    _llm_shell_detect
    [[ -z "$LLM_SHELL_BACKEND" ]] && return 1
    
    if [[ ! -f "$LLM_SHELL_CONFIG" ]]; then
        echo -e "${YELLOW}⚠️ 需要配置API Key${RESET}"
        return 1
    fi
    
    if [[ "$LLM_SHELL_BACKEND" == *.py ]]; then
        local pkg_dir
        pkg_dir="$(cd "$(dirname "$LLM_SHELL_BACKEND")/.." && pwd)"
        (cd "$pkg_dir" && $LLM_SHELL_PYTHON -m llm_shell.main --generate "$desc") 2>/dev/null
    else
        llm-shell --generate "$desc" 2>/dev/null
    fi
}

# 编辑命令
_llm_shell_edit() {
    local cmd="$1"
    local tmpfile="$(mktemp)"
    echo "$cmd" > "$tmpfile"
    ${EDITOR:-vim} "$tmpfile"
    cat "$tmpfile" 2>/dev/null | tr -d '\n'
    rm -f "$tmpfile"
}

# 危险检查
_llm_shell_danger() {
    [[ "$1" == *"rm -rf /"* ]] && return 0
    [[ "$1" == *"rm -rf /*"* ]] && return 0
    return 1
}

# 主处理函数
,() {
    # 获取描述（所有参数）
    local desc="$*"
    
    if [[ -z "$desc" ]]; then
        echo -e "${YELLOW}用法: , <描述>${RESET}"
        return 1
    fi
    
    echo -e "${DIM}🤔 思考中...${RESET}"
    local cmd=$(_llm_shell_gen "$desc")
    
    if [[ -z "$cmd" ]]; then
        echo -e "${RED}❌ 生成失败${RESET}"
        return 1
    fi
    
    echo -e "${CYAN}➜ $cmd${RESET}"
    echo -n "执行? [Y/n/e] "
    read -n 1 response
    echo
    
    case "$response" in
        n|N) echo -e "${YELLOW}已取消${RESET}"; return 1 ;;
        e|E)
            cmd=$(_llm_shell_edit "$cmd")
            [[ -z "$cmd" ]] && { echo -e "${YELLOW}已取消${RESET}"; return 1; }
            echo -e "${CYAN}✎ $cmd${RESET}"
            ;;
    esac
    
    if _llm_shell_danger "$cmd"; then
        echo -e "${RED}⚠️ 危险命令！${RESET}"
        echo -n "确定? [y/N] "
        read -n 1 confirm
        echo
        [[ ! "$confirm" =~ ^[Yy]$ ]] && return 1
    fi
    
    echo -e "${GREEN}$ $cmd${RESET}"
    eval "$cmd"
}

# 编辑模式
,,() {
    local desc="$*"
    
    if [[ -z "$desc" ]]; then
        echo -e "${YELLOW}用法: ,, <描述>${RESET}"
        return 1
    fi
    
    echo -e "${DIM}🤔 思考中...${RESET}"
    local cmd=$(_llm_shell_gen "$desc")
    
    if [[ -z "$cmd" ]]; then
        echo -e "${RED}❌ 生成失败${RESET}"
        return 1
    fi
    
    echo -e "${CYAN}➜ $cmd${RESET}"
    cmd=$(_llm_shell_edit "$cmd")
    
    [[ -z "$cmd" ]] && { echo -e "${YELLOW}已取消${RESET}"; return 1; }
    echo -e "${CYAN}✎ $cmd${RESET}"
    
    echo -n "执行? [Y/n] "
    read -n 1 response
    echo
    
    [[ "$response" =~ ^[Nn]$ ]] && { echo -e "${YELLOW}已取消${RESET}"; return 1; }
    
    if _llm_shell_danger "$cmd"; then
        echo -e "${RED}⚠️ 危险命令！${RESET}"
        echo -n "确定? [y/N] "
        read -n 1 confirm
        echo
        [[ ! "$confirm" =~ ^[Yy]$ ]] && return 1
    fi
    
    echo -e "${GREEN}$ $cmd${RESET}"
    eval "$cmd"
}

# fuck 修复
fuck() {
    _llm_shell_detect
    [[ -z "$LLM_SHELL_BACKEND" ]] && return 1
    
    local last=$(history 1 | sed 's/^[[:space:]]*[0-9]*[[:space:]]*//')
    [[ -z "$last" ]] && return 1
    [[ "$last" == "fuck" ]] && return 1
    
    echo -e "${YELLOW}🤔 修复: $last${RESET}"
    
    local fixed
    if [[ "$LLM_SHELL_BACKEND" == *.py ]]; then
        local pkg_dir
        pkg_dir="$(cd "$(dirname "$LLM_SHELL_BACKEND")/.." && pwd)"
        fixed=$((cd "$pkg_dir" && $LLM_SHELL_PYTHON -m llm_shell.main --fix "$last") 2>/dev/null)
    else
        fixed=$(llm-shell --fix "$last" 2>/dev/null)
    fi
    
    [[ -z "$fixed" ]] && { echo -e "${RED}无法修复${RESET}"; return 1; }
    
    echo -e "${CYAN}🔧 $fixed${RESET}"
    echo -n "执行? [Y/n] "
    read -n 1 response
    echo
    
    [[ "$response" =~ ^[Nn]$ ]] && return 1
    
    echo -e "${GREEN}$ $fixed${RESET}"
    eval "$fixed"
}


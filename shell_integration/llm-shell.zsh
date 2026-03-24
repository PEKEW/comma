#!/bin/zsh
# llm-shell-minimal.zsh - 最小化zsh集成
# 使用方法: source /path/to/llm-shell-minimal.zsh

export LLM_SHELL_DIR="${LLM_SHELL_DIR:-$HOME/.config/llm-shell}"
export LLM_SHELL_PYTHON="${LLM_SHELL_PYTHON:-python3}"

# 在脚本顶层（source 时）捕获脚本目录，此时 $0 是脚本路径
# 注意：函数内部 $0 是函数名，所以必须在函数外捕获
_LLM_SHELL_SCRIPT_DIR="${0:A:h}"

# 检测后端
_llm_shell_backend() {
    if [[ -z "$LLM_SHELL_BACKEND" ]]; then
        local d="$_LLM_SHELL_SCRIPT_DIR"
        if [[ -f "$d/../llm_shell/main.py" ]]; then
            export LLM_SHELL_BACKEND="$d/../llm_shell/main.py"
        elif command -v llm-shell &>/dev/null; then
            export LLM_SHELL_BACKEND="llm-shell"
        fi
    fi
}

# 生成命令
_llm_shell_gen() {
    _llm_shell_backend
    [[ -z "$LLM_SHELL_BACKEND" ]] && return 1
    
    if [[ "$LLM_SHELL_BACKEND" == *.py ]]; then
        # 必须用 -m 模块方式运行，否则相对导入（from .config import ...）会失败
        local pkg_dir="${LLM_SHELL_BACKEND:A:h:h}"  # main.py -> llm_shell/ -> 项目根目录
        (cd "$pkg_dir" && $LLM_SHELL_PYTHON -m llm_shell.main --generate "$1") 2>/dev/null
    else
        llm-shell --generate "$1" 2>/dev/null
    fi
}

# 主命令 - 使用 lsh 别名而不是 ,
lsh() {
    local desc="$*"
    [[ -z "$desc" ]] && { echo "用法: lsh <描述>"; return 1; }
    
    echo "🤔 思考中..."
    local cmd=$(_llm_shell_gen "$desc")
    [[ -z "$cmd" ]] && { echo "❌ 生成失败"; return 1; }
    
    echo "➜ $cmd"
    echo -n "执行? [Y/n] "
    read -k 1 r; local read_ret=$?
    stty sane 2>/dev/null  # 确保终端状态正常（防止 read -k 被中断后 echo 关闭）
    echo
    [[ $read_ret -ne 0 || "$r" == "n" ]] && { echo "已取消"; return 1; }

    echo "\$ $cmd"
    eval "$cmd"
}

# 编辑模式
lsh-edit() {
    local desc="$*"
    [[ -z "$desc" ]] && { echo "用法: lsh-edit <描述>"; return 1; }
    
    echo "🤔 思考中..."
    local cmd=$(_llm_shell_gen "$desc")
    [[ -z "$cmd" ]] && { echo "❌ 生成失败"; return 1; }
    
    echo "➜ $cmd"
    local tmp=$(mktemp)
    echo "$cmd" > "$tmp"
    ${EDITOR:-vim} "$tmp"
    cmd=$(cat "$tmp" | tr -d '\n')
    rm -f "$tmp"
    
    [[ -z "$cmd" ]] && { echo "已取消"; return 1; }
    echo "✎ $cmd"
    echo -n "执行? [Y/n] "
    read -k 1 r; local read_ret=$?
    stty sane 2>/dev/null
    echo
    [[ $read_ret -ne 0 || "$r" == "n" ]] && { echo "已取消"; return 1; }

    echo "\$ $cmd"
    eval "$cmd"
}

# 修复
fuck() {
    _llm_shell_backend
    local last=$(fc -ln -1 | sed 's/^[[:space:]]*//')
    [[ "$last" == "fuck" ]] && return 1
    
    echo "🤔 修复: $last"
    local fixed
    if [[ "$LLM_SHELL_BACKEND" == *.py ]]; then
        local pkg_dir="${LLM_SHELL_BACKEND:A:h:h}"
        fixed=$((cd "$pkg_dir" && $LLM_SHELL_PYTHON -m llm_shell.main --fix "$last") 2>/dev/null)
    else
        fixed=$(llm-shell --fix "$last" 2>/dev/null)
    fi
    
    [[ -z "$fixed" ]] && { echo "无法修复"; return 1; }
    echo "🔧 $fixed"
    echo -n "执行? [Y/n] "
    read -k 1 r; local read_ret=$?
    stty sane 2>/dev/null
    echo
    [[ $read_ret -ne 0 || "$r" == "n" ]] && return 1
    echo "\$ $fixed"
    eval "$fixed"
}

# 如果要用逗号，创建别名
alias ,='lsh'
alias ,,='lsh-edit'


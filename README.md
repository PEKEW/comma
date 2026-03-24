# comma

> natural shell with natural interaction way

Shell 里有些命令就是记不住——`find` 的参数、`awk` 的写法、`tar` 到底是 `xvzf` 还是 `xvjf`。遇到这类情况，通常要切出去问 LLM，再复制回来，打断了思路。

llm-shell 在 shell 里原地解决这个问题：用 `,` 开头描述意图，LLM 返回命令，确认后执行，不用离开终端。

```
❯ , 查找当前目录下大于 100MB 的文件
🤔 思考中...
➜ find . -type f -size +100M
执行? [Y/n] y
$ find . -type f -size +100M
./data/dataset.tar.gz
```

---

## 为什么不直接问 ChatGPT / Claude

可以，但每次需要：打开浏览器或 app → 描述问题 → 等回答 → 复制命令 → 切回终端 → 粘贴执行。如果命令不对还要再来一遍。

llm-shell 把这个往返压缩成一次按键，而且只请求命令本身，prompt 极短，消耗 token 很少。

---

## `fuck` — 命令写错了直接修

继承自 [thefuck](https://github.com/nvbn/thefuck) 的思路，但实现更简单：不维护规则库，直接把出错的命令和错误信息丢给 LLM，让它给出修正。覆盖范围更广，包括 typo、参数写错、命令不存在等各种情况。

```
❯ git statsu
git: 'statsu' is not a git command.

❯ fuck
🤔 修复: git statsu
🔧 git status
执行? [Y/n] y
$ git status
On branch main...
```

---

## 用法

| 触发方式 | 说明 |
|---------|------|
| `, <描述>` | 生成命令，确认后执行 |
| `,, <描述>` | 生成命令，在 `$EDITOR` 中修改后执行 |
| `fuck` | 修复上一条失败的命令 |

其余命令照常执行，不受影响。

### 示例

```
❯ , 显示 git 最近 5 条提交的单行日志
❯ , 找出占用 8080 端口的进程
❯ , 把 jpg 全部转成 webp，保留原图
❯ ,, 递归删除所有 node_modules      # 打开编辑器确认再执行
```

---

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/yourname/comma.git
cd comma
```

### 2. 添加到 shell 配置

**zsh** — 在 `~/.zshrc` 中追加：

```zsh
source /path/to/llm-shell/shell_integration/llm-shell.zsh
```

**bash** — 在 `~/.bashrc` 中追加：

```bash
source /path/to/llm-shell/shell_integration/llm-shell.bash
```

### 3. 配置 API

```bash
mkdir -p ~/.config/llm-shell
cp config.example.json ~/.config/llm-shell/config.json
# 编辑填入 api_key、api_base、model
```

### 4. 重载 shell

```bash
source ~/.zshrc   # 或 source ~/.bashrc
```

---

## 配置

配置文件：`~/.config/llm-shell/config.json`

```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "api_base": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "editor": "vim",
  "timeout": 30
}
```

常用服务参考：

| 服务 | `api_base` | 推荐 `model` |
|------|-----------|-------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Moonshot (国内) | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Moonshot (国际) | `https://api.moonshot.ai/v1` | `moonshot-v1-8k` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3` |

---

## 依赖

- Python 3.7+
- zsh 或 bash
- 能访问所配置 API 的网络

无需额外安装 Python 包，使用标准库 `urllib`。

---

## 项目结构

```
llm-shell/
├── llm_shell/
│   ├── main.py          # CLI 入口，命令生成/修复逻辑
│   ├── llm_client.py    # LLM API 客户端
│   ├── config.py        # 配置管理
│   └── utils.py         # 工具函数
├── shell_integration/
│   ├── llm-shell.zsh    # zsh 集成
│   └── llm-shell.bash   # bash 集成
├── setup.py
└── config.example.json
```

---

## License

MIT

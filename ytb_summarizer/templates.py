"""Built-in prompt templates for summarization."""
from __future__ import annotations

import os
import yaml
from pathlib import Path

# ── Built-in templates ──────────────────────────────────────────────────────

BUILTIN_TEMPLATES: dict[str, dict] = {
    "default": {
        "name": "default",
        "description": "通用视频总结",
        "prompt": """\
请根据以下 YouTube 视频的字幕内容，生成一份结构化的中文总结报告。

视频标题：{title}
视频 URL：{url}

字幕内容：
{transcript}

请按以下结构输出 Markdown 格式报告：

# {title}

## 📋 概述
（2-3 句话概括视频核心内容）

## 🎯 主要要点
-
-
-

## 📚 主要话题
（分小节展开每个主要话题）

## 💡 关键收获
（读者看完后应该记住的最重要的3-5点）

## 🔗 提到的资源
（视频中提到的工具、网站、书籍等，如无则省略此节）
""",
    },
    "course": {
        "name": "course",
        "description": "课程/系列教程总结",
        "prompt": """\
请根据以下课程/教程视频的字幕内容，生成详细的中文学习笔记。

视频标题：{title}
视频 URL：{url}

字幕内容：
{transcript}

请按以下结构输出 Markdown 格式报告：

# {title}

## 📚 前置知识
（学习本课程需要了解的基础知识）

## 🗂️ 课程结构
（课程的主要章节/模块概览）

## 🧠 核心概念
（本课程中的关键概念和定义）

## 📝 操作步骤
（如有实操内容，列出具体步骤）

## ❓ 复习题
（根据内容生成3-5个自测问题）

## 📌 总结
（一段话总结课程价值）
""",
    },
    "talk": {
        "name": "talk",
        "description": "TED/演讲/讲座总结",
        "prompt": """\
请根据以下演讲/讲座视频的字幕内容，生成深度中文分析报告。

视频标题：{title}
视频 URL：{url}

字幕内容：
{transcript}

请按以下结构输出 Markdown 格式报告：

# {title}

## 👤 演讲者
（演讲者姓名、背景介绍，如字幕中有提及）

## 💬 核心论点
（演讲的中心思想，1-2句话）

## 🔍 主要论据
（支持核心论点的关键论据和案例）

## ✨ 金句摘录
> （直接引用演讲中的精彩语句）

## 🎯 结论与行动号召
（演讲的结论和对观众的呼吁）

## 💭 我的思考
（这个演讲最值得深思的地方）
""",
    },
    "tech-tutorial": {
        "name": "tech-tutorial",
        "description": "编程/DevOps 技术教程",
        "prompt": """\
请根据以下技术教程视频的字幕内容，生成实用的中文技术笔记。

视频标题：{title}
视频 URL：{url}

字幕内容：
{transcript}

请按以下结构输出 Markdown 格式报告（代码块使用正确的语言标记）：

# {title}

## 🔧 环境要求
（系统要求、依赖版本等）

## 📦 安装命令
```bash
# 安装相关命令
```

## 🚀 分步实现
（详细步骤，含代码块）

## ⚠️ 常见报错与解决方案
| 报错 | 原因 | 解决方法 |
|------|------|---------|

## 📋 快速参考
（命令速查表或关键代码片段汇总）
""",
    },
}


def get_builtin_template_names() -> list[str]:
    return list(BUILTIN_TEMPLATES.keys())


def get_template(name: str, custom_dir: Path | None = None) -> dict:
    """Load a template by name. Custom templates override built-ins."""
    if custom_dir:
        custom_path = custom_dir / f"{name}.yaml"
        if custom_path.exists():
            with open(custom_path, encoding="utf-8") as f:
                return yaml.safe_load(f)

    if name in BUILTIN_TEMPLATES:
        return BUILTIN_TEMPLATES[name]

    raise ValueError(f"Template '{name}' not found.")


def list_templates(custom_dir: Path | None = None) -> list[str]:
    """Return all available template names (built-in + custom)."""
    names = set(BUILTIN_TEMPLATES.keys())
    if custom_dir and custom_dir.exists():
        for f in custom_dir.glob("*.yaml"):
            names.add(f.stem)
    return sorted(names)


def render_prompt(template: dict, title: str, url: str, transcript: str) -> str:
    """Fill template variables."""
    return template["prompt"].format(
        title=title,
        url=url,
        transcript=transcript[:50000],  # safety truncation
    )


def export_builtin_to_dir(directory: Path) -> None:
    """Write built-in templates as YAML files to directory (for user editing)."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, tmpl in BUILTIN_TEMPLATES.items():
        path = directory / f"{name}.yaml"
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(tmpl, f, allow_unicode=True, default_flow_style=False)

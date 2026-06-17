#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - 文件日志 + 终端彩色日志
支持 DEBUG/INFO/SUCCESS/WARNING/ERROR 五级日志
"""

import os
import time
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.text import Text

console = Console()

# 日志级别
LEVEL_DEBUG = 0
LEVEL_INFO = 1
LEVEL_SUCCESS = 2
LEVEL_WARNING = 3
LEVEL_ERROR = 4

LEVEL_NAMES = {
    LEVEL_DEBUG: "DEBUG",
    LEVEL_INFO: "INFO",
    LEVEL_SUCCESS: "SUCCESS",
    LEVEL_WARNING: "WARNING",
    LEVEL_ERROR: "ERROR",
}

LEVEL_COLORS = {
    LEVEL_DEBUG: "dim white",
    LEVEL_INFO: "cyan",
    LEVEL_SUCCESS: "bold green",
    LEVEL_WARNING: "bold yellow",
    LEVEL_ERROR: "bold red",
}

# 日志文件路径
from .paths import LOG_DIR
LOG_FILE = None

# 当前日志级别（默认DEBUG，记录所有）
_current_level = LEVEL_DEBUG

# 是否输出到终端
_console_output = True

# 是否输出到文件
_file_output = True


def _ensure_log_dir():
    """确保日志目录存在"""
    global LOG_FILE
    if LOG_FILE is None:
        os.makedirs(LOG_DIR, exist_ok=True)
        LOG_FILE = f"{LOG_DIR}/andwrebox_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


def set_level(level: int):
    """设置日志级别"""
    global _current_level
    _current_level = level


def set_console_output(enabled: bool):
    """设置是否输出到终端"""
    global _console_output
    _console_output = enabled


def set_file_output(enabled: bool):
    """设置是否输出到文件"""
    global _file_output
    _file_output = enabled


def _write_log(level: int, module: str, message: str):
    """写入日志"""
    if level < _current_level:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_name = LEVEL_NAMES.get(level, "UNKNOWN")
    color = LEVEL_COLORS.get(level, "white")
    
    # 终端输出
    if _console_output:
        prefix = f"[{timestamp}] [{level_name}] [{module}]"
        # 转义消息中的方括号，防止 Rich 将其误解析为标记
        safe_message = message.replace("[", "\\[").replace("]", "\\]")
        console.print(f"[{color}]{prefix}[/] {safe_message}")
    
    # 文件输出
    if _file_output:
        _ensure_log_dir()
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [{level_name}] [{module}] {message}\n")
        except Exception:
            pass


def debug(module: str, message: str):
    """调试日志"""
    _write_log(LEVEL_DEBUG, module, message)


def info(module: str, message: str):
    """信息日志"""
    _write_log(LEVEL_INFO, module, message)


def success(module: str, message: str):
    """成功日志"""
    _write_log(LEVEL_SUCCESS, module, message)


def warning(module: str, message: str):
    """警告日志"""
    _write_log(LEVEL_WARNING, module, message)


def error(module: str, message: str):
    """错误日志"""
    _write_log(LEVEL_ERROR, module, message)


def log_exception(module: str, e: Exception):
    """记录异常详情"""
    import traceback
    tb = traceback.format_exc()
    error(module, f"Exception: {str(e)}")
    if _file_output:
        _ensure_log_dir()
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n--- TRACEBACK ---\n{tb}\n--- END TRACEBACK ---\n\n")
        except Exception:
            pass


def get_log_file() -> Optional[str]:
    """获取当前日志文件路径"""
    _ensure_log_dir()
    return LOG_FILE


def dump_recent(n: int = 20):
    """打印最近N条日志"""
    _ensure_log_dir()
    if LOG_FILE and os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                console.print(f"\n[bold cyan]Recent {min(n, len(lines))} log entries:[/]")
                for line in lines[-n:]:
                    console.print(f"  [dim]{line.rstrip()}[/]")
        except Exception:
            console.print("[dim]No logs available[/]")
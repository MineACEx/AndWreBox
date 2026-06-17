#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0 - 统一路径管理
数据目录: /data/andwrebox/     (Android 系统分区，普通用户不可见)
临时目录: /data/local/tmp/andwrebox/  (系统临时分区)
模块输出: 用户可自定义，默认 /sdcard/AndWreBox/output/
"""

import os
import json

# ── 内部数据目录（/data 分区，用户无法通过文件管理器看到）──
DATA_DIR      = "/data/andwrebox"
AUTH_DIR      = "/data/andwrebox/auth"
CONFIG_DIR    = "/data/andwrebox/config"
BACKUP_DIR    = "/data/andwrebox/backups"
LOG_DIR       = "/data/andwrebox/logs"

# ── 临时缓存目录（/data/local/tmp 系统级临时目录）──
TMP_DIR       = "/data/local/tmp/andwrebox"

# ── 密码相关文件（独立存储，安全隔离）──
AUTH_FILE         = os.path.join(AUTH_DIR, "auth.enc")
AUTH_TOKEN_FILE   = os.path.join(AUTH_DIR, ".token.enc")

# ── 非密码配置合并文件（disclaimer + lang + settings 合一）──
CONFIG_FILE       = os.path.join(CONFIG_DIR, "config.enc")

# ── 模块输出目录（用户可见，默认 /sdcard）──
_MODULE_OUTPUT_SETTINGS = os.path.join(CONFIG_DIR, "module_path.enc")
DEFAULT_MODULE_OUTPUT   = "/sdcard/AndWreBox/output"


def get_module_output_dir():
    """获取模块输出目录（从配置读取，回退默认值）"""
    try:
        from .crypto import decrypt_string
        path = decrypt_string(_MODULE_OUTPUT_SETTINGS)
        if path and os.path.isabs(path):
            return path
    except Exception:
        pass
    return DEFAULT_MODULE_OUTPUT


def set_module_output_dir(path: str):
    """设置模块输出目录"""
    from .crypto import encrypt_string
    return encrypt_string(_MODULE_OUTPUT_SETTINGS, path)


def ensure_all_dirs():
    """确保所有必要目录存在"""
    for d in [DATA_DIR, AUTH_DIR, CONFIG_DIR, BACKUP_DIR, LOG_DIR, TMP_DIR]:
        os.makedirs(d, exist_ok=True)
    # 确保模块输出目录
    out = get_module_output_dir()
    os.makedirs(out, exist_ok=True)


def clean_tmp():
    """清理临时文件"""
    import shutil
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR, ignore_errors=True)
        os.makedirs(TMP_DIR, exist_ok=True)
    return True


def get_project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
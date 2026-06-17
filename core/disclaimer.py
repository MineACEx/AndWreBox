#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0 - 免责协议 + 统一配置模块
v1.0: 所有非密码配置合并到 /data/andwrebox/config/config.enc
"""

from datetime import datetime
from .paths import CONFIG_FILE
from .crypto import decrypt_json, encrypt_json

DISCLAIMER_TEXT_ZH = """
╔══════════════════════════════════════════════════════════════╗
║                    【免责协议 · 请仔细阅读】                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. 本工具(AndWreBox 安卓扳手盒子)仅供学习和研究使用。         ║
║                                                              ║
║  2. 使用本工具修改系统底层参数可能导致:                          ║
║     · 系统不稳定、无法开机、数据丢失                            ║
║     · 硬件损坏(如过热导致CPU/GPU永久性损伤)                     ║
║     · 失去官方保修资格                                         ║
║     · 违反厂商服务条款                                         ║
║                                                              ║
║  3. 用户应自行承担使用本工具的全部风险和后果。                   ║
║     开发者不承担任何因使用本工具造成的直接或间接损失。           ║
║                                                              ║
║  4. 请勿将设备伪装功能用于非法用途。                            ║
║                                                              ║
║  5. 使用本工具即表示您已年满18周岁。                            ║
║                                                              ║
║  6. 本工具不会收集、上传任何用户数据。                          ║
║     所有数据加密存储在 /data/andwrebox/ 目录下。               ║
║                                                              ║
║  7. 继续使用即表示您已阅读、理解并同意以上全部条款。             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

DISCLAIMER_TEXT_EN = """
╔══════════════════════════════════════════════════════════════╗
║                   【DISCLAIMER · READ CAREFULLY】              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. This tool (AndWreBox) is for educational purposes only.  ║
║                                                              ║
║  2. Modifying system-level parameters may cause:             ║
║     · System instability, boot failure, data loss            ║
║     · Hardware damage (CPU/GPU permanent damage)             ║
║     · Loss of official warranty                              ║
║                                                              ║
║  3. Users assume ALL risks. The developer bears NO           ║
║     responsibility for any damages.                          ║
║                                                              ║
║  4. Do NOT use spoofing for illegal purposes.                ║
║                                                              ║
║  5. By using this tool, you confirm you are 18+.             ║
║                                                              ║
║  6. No user data is collected. All data is encrypted in      ║
║     /data/andwrebox/.                                        ║
║                                                              ║
║  7. Continuing means you agree to ALL terms.                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def _load_config() -> dict:
    """加载统一配置"""
    return decrypt_json(CONFIG_FILE)


def _save_config(config: dict) -> bool:
    """保存统一配置"""
    return encrypt_json(CONFIG_FILE, config)


def _get_or_create_config() -> dict:
    """获取配置，不存在则创建"""
    config = _load_config()
    if not config:
        config = {"version": "1.0"}
    return config


# ── 免责协议 ──

def is_disclaimer_accepted() -> bool:
    config = _load_config()
    return config.get("disclaimer_accepted", False)


def get_disclaimer_text(lang: str = "zh") -> str:
    return DISCLAIMER_TEXT_ZH if lang == "zh" else DISCLAIMER_TEXT_EN


def accept_disclaimer() -> bool:
    config = _get_or_create_config()
    config["disclaimer_accepted"] = True
    config["disclaimer_accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return _save_config(config)


# ── 语言设置 ──

def load_language() -> str:
    config = _load_config()
    return config.get("language", "zh")


def save_language(lang: str) -> bool:
    config = _get_or_create_config()
    config["language"] = lang
    return _save_config(config)


# ── 模块输出路径 ──

def load_module_output_path() -> str:
    from .paths import DEFAULT_MODULE_OUTPUT
    config = _load_config()
    return config.get("module_output_path", DEFAULT_MODULE_OUTPUT)


def save_module_output_path(path: str) -> bool:
    config = _get_or_create_config()
    config["module_output_path"] = path
    return _save_config(config)


# ── AnyKernel3 答题验证 ──

def is_ak3_quiz_passed() -> bool:
    """检查是否已通过AK3答题验证"""
    config = _load_config()
    return config.get("ak3_quiz_passed", False)

def set_ak3_quiz_passed() -> bool:
    """标记AK3答题已通过（答对一次后调用）"""
    config = _get_or_create_config()
    config["ak3_quiz_passed"] = True
    return _save_config(config)

def is_ak3_skip_quiz() -> bool:
    """检查是否开启免答题"""
    config = _load_config()
    return config.get("ak3_skip_quiz", False)

def set_ak3_skip_quiz(enabled: bool) -> bool:
    """设置免答题开关"""
    config = _get_or_create_config()
    config["ak3_skip_quiz"] = enabled
    return _save_config(config)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0 - 用户认证模块
支持: 首次注册、密码登录、自动验证开关、SHA256密码哈希
v1.0: 数据加密存储，密钥基于设备指纹，防止通过删除文件绕过认证
"""

import os
import hashlib
import secrets
from datetime import datetime

from .paths import AUTH_FILE, AUTH_TOKEN_FILE
from .crypto import encrypt_json, decrypt_json, encrypt_string, decrypt_string


def _hash_password(password: str, salt: str = None) -> tuple:
    """SHA256 密码哈希，返回 (hash, salt)"""
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return h, salt


def _generate_token():
    """生成自动验证令牌"""
    return secrets.token_hex(32)


# ============ 公开API ============

def is_registered():
    """检查是否已注册"""
    config = decrypt_json(AUTH_FILE)
    return bool(config.get("password_hash"))


def is_auto_verify_enabled():
    """检查自动验证是否开启"""
    token = decrypt_string(AUTH_TOKEN_FILE)
    if not token:
        return False
    config = decrypt_json(AUTH_FILE)
    return config.get("token") == token


def register_user(password: str) -> bool:
    """
    注册新用户
    返回 True 成功, False 失败
    """
    if is_registered():
        return False

    if len(password) < 4:
        return False

    pwd_hash, salt = _hash_password(password)
    token = _generate_token()

    config = {
        "password_hash": pwd_hash,
        "salt": salt,
        "token": token,
        "auto_verify": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0"
    }

    if encrypt_json(AUTH_FILE, config):
        encrypt_string(AUTH_TOKEN_FILE, token)
        return True
    return False


def verify_password(password: str) -> bool:
    """
    验证密码
    返回 True 验证通过, False 密码错误
    """
    config = decrypt_json(AUTH_FILE)
    if not config.get("password_hash"):
        return False

    pwd_hash, _ = _hash_password(password, config.get("salt", ""))
    return pwd_hash == config["password_hash"]


def login_with_token() -> bool:
    """使用令牌自动登录"""
    return is_auto_verify_enabled()


def enable_auto_verify():
    """开启自动验证"""
    config = decrypt_json(AUTH_FILE)
    if not config:
        return False
    config["auto_verify"] = True
    encrypt_json(AUTH_FILE, config)
    encrypt_string(AUTH_TOKEN_FILE, config.get("token", ""))
    return True


def disable_auto_verify():
    """关闭自动验证"""
    config = decrypt_json(AUTH_FILE)
    if not config:
        return False
    config["auto_verify"] = False
    encrypt_json(AUTH_FILE, config)
    try:
        os.remove(AUTH_TOKEN_FILE)
    except Exception:
        pass
    return True


def reset_password(old_password: str, new_password: str) -> bool:
    """重置密码"""
    if not verify_password(old_password):
        return False
    if len(new_password) < 4:
        return False

    config = decrypt_json(AUTH_FILE)
    pwd_hash, salt = _hash_password(new_password)
    config["password_hash"] = pwd_hash
    config["salt"] = salt
    encrypt_json(AUTH_FILE, config)
    return True
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0 - 数据加密模块
AES-256-CBC + PBKDF2 密钥派生，密钥基于设备指纹
防止用户通过日期筛选删除数据文件来跳过认证
"""

import os
import json
import hashlib
import base64
import secrets
from typing import Optional

# ── 尝试导入 cryptography ──
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False

# ── 密钥派生 ──
# 使用设备唯一标识 + 固定盐值派生密钥，确保每台设备密钥不同
# 即使数据文件被拷贝到其他设备也无法解密
_FIXED_SALT = b"AndWreBox_Snapdragon_Elite_2026_Kryo_Oryon"

def _get_device_key() -> bytes:
    """
    基于设备指纹派生32字节AES密钥
    使用: 序列号 + 型号 + 固定盐
    """
    try:
        # 尝试获取设备序列号
        import subprocess
        r = subprocess.run(["getprop", "ro.serialno"], capture_output=True, text=True, timeout=3)
        serial = r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        serial = "unknown"

    try:
        r = subprocess.run(["getprop", "ro.product.model"], capture_output=True, text=True, timeout=3)
        model = r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        model = "unknown"

    key_material = f"{serial}:{model}".encode()
    return hashlib.pbkdf2_hmac("sha256", key_material, _FIXED_SALT, 100000, dklen=32)


def _encrypt_data(plaintext: str) -> Optional[str]:
    """
    AES-256-CBC 加密，返回 base64 编码的密文
    如果 cryptography 不可用，回退到简单 XOR 混淆
    """
    if not _CRYPTO_AVAILABLE:
        return _xor_obfuscate(plaintext)

    try:
        key = _get_device_key()
        iv = secrets.token_bytes(16)

        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        # iv + ciphertext，base64 编码
        result = base64.b64encode(iv + ciphertext).decode("ascii")
        return result
    except Exception:
        return _xor_obfuscate(plaintext)


def _decrypt_data(ciphertext_b64: str) -> Optional[str]:
    """
    AES-256-CBC 解密，输入 base64 编码的密文
    """
    if not _CRYPTO_AVAILABLE:
        return _xor_deobfuscate(ciphertext_b64)

    try:
        key = _get_device_key()
        raw = base64.b64decode(ciphertext_b64)

        if len(raw) < 32:  # 至少 iv(16) + 1 block(16)
            return _xor_deobfuscate(ciphertext_b64)

        iv = raw[:16]
        ciphertext = raw[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
        return plaintext.decode("utf-8")
    except Exception:
        return _xor_deobfuscate(ciphertext_b64)


def _xor_obfuscate(data: str) -> str:
    """
    简单XOR混淆（无 cryptography 时的回退方案）
    使用设备密钥进行XOR，使得数据不以明文存储
    """
    key = _get_device_key()
    data_bytes = data.encode("utf-8")
    result = bytes(b ^ key[i % len(key)] for i, b in enumerate(data_bytes))
    return base64.b64encode(result).decode("ascii")


def _xor_deobfuscate(encoded: str) -> Optional[str]:
    """XOR解混淆"""
    try:
        key = _get_device_key()
        raw = base64.b64decode(encoded)
        result = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
        return result.decode("utf-8")
    except Exception:
        return None


# ── 公开 API：加密读写 JSON ──

def encrypt_json(path: str, data: dict) -> bool:
    """加密保存 JSON 数据"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        plaintext = json.dumps(data, ensure_ascii=False, indent=2)
        ciphertext = _encrypt_data(plaintext)
        if ciphertext is None:
            # 加密失败，回退到明文存储
            with open(path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        with open(path, "w") as f:
            f.write(ciphertext)
        return True
    except Exception:
        return False


def decrypt_json(path: str) -> dict:
    """解密读取 JSON 数据"""
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            content = f.read().strip()
        if not content:
            return {}
        # 尝试 base64 解码（判断是否加密）
        try:
            base64.b64decode(content)
            plaintext = _decrypt_data(content)
            if plaintext:
                return json.loads(plaintext)
        except Exception:
            pass
        # 回退：明文 JSON
        return json.loads(content)
    except Exception:
        return {}


def encrypt_string(path: str, data: str) -> bool:
    """加密保存字符串"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        ciphertext = _encrypt_data(data)
        if ciphertext is None:
            with open(path, "w") as f:
                f.write(data)
            return True
        with open(path, "w") as f:
            f.write(ciphertext)
        return True
    except Exception:
        return False


def decrypt_string(path: str) -> str:
    """解密读取字符串"""
    try:
        if not os.path.exists(path):
            return ""
        with open(path, "r") as f:
            content = f.read().strip()
        if not content:
            return ""
        try:
            base64.b64decode(content)
            plaintext = _decrypt_data(content)
            if plaintext:
                return plaintext
        except Exception:
            pass
        return content
    except Exception:
        return ""


def obfuscate_filename(name: str) -> str:
    """
    对文件名进行混淆（SHA256前16位），防止通过文件名猜测内容
    用于 tmp 目录中的缓存文件
    """
    h = hashlib.sha256(name.encode()).hexdigest()[:16]
    return h
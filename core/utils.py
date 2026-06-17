#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数 - 设备信息采集、依赖检查、备份管理
"""

import os
import sys
import shutil
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, Optional

from .config import DEVICE_INFO, CONFIG_DIR, OUTPUT_DIR, BACKUP_DIR, LOG_DIR, SNAPDRAGON_PATHS, SNAPDRAGON_DETECT_MAP
from .shell import shell


def ensure_dirs():
    """确保必要的目录存在"""
    for d in [CONFIG_DIR, OUTPUT_DIR, BACKUP_DIR, LOG_DIR]:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


# ============ DPI / 终端宽度自适应 ============
def get_terminal_size() -> tuple:
    """
    获取终端尺寸 (宽度, 高度)
    优先使用 shutil，失败则回退到 os.environ
    """
    try:
        cols, rows = shutil.get_terminal_size((80, 24))
        return cols, rows
    except Exception:
        pass
    try:
        cols = int(os.environ.get("COLUMNS", 80))
        rows = int(os.environ.get("LINES", 24))
        return cols, rows
    except Exception:
        return 80, 24


def get_adaptive_width() -> int:
    """
    获取自适应面板宽度
    窄屏(<60列)→48, 中屏(60-90)→60, 宽屏(90-120)→68, 超宽→72
    """
    cols, _ = get_terminal_size()
    if cols < 60:
        return 48
    if cols < 90:
        return 60
    if cols < 120:
        return 68
    return 72


def get_adaptive_table_width() -> tuple:
    """获取自适应表格列宽 (label_col, value_col)"""
    cols, _ = get_terminal_size()
    if cols < 60:
        return (10, 30)
    if cols < 90:
        return (12, 36)
    if cols < 120:
        return (16, 40)
    return (18, 48)


def check_dependencies() -> bool:
    """检查并自动安装缺失的Python依赖"""
    required = {
        "rich": "rich",
        "colorama": "colorama",
        "blessed": "blessed",
        "pyfiglet": "pyfiglet",
    }
    missing = []
    for mod, pip_name in required.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"\n检测到缺失依赖: {', '.join(missing)}")
        print("正在自动安装...")
        for pkg in missing:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg, "--break-system-packages", "-q"],
                    check=True, timeout=60
                )
                print(f"  ✓ {pkg} 安装成功")
            except Exception as e:
                print(f"  ✗ {pkg} 安装失败: {e}")
                return False
    return True


def collect_device_info() -> Dict[str, str]:
    """采集设备完整信息"""
    info = DEVICE_INFO.copy()

    info["model"] = shell.get_prop("ro.product.model")
    info["manufacturer"] = shell.get_prop("ro.product.manufacturer")
    info["android_version"] = shell.get_prop("ro.build.version.release")
    info["sdk_version"] = shell.get_prop("ro.build.version.sdk")
    info["build_fingerprint"] = shell.get_prop("ro.build.fingerprint")
    info["rom_name"] = _detect_rom()

    # 内核信息
    ok, out, _ = shell.run("uname -r")
    info["kernel_version"] = out.strip() if ok else "unknown"

    # CPU信息
    ok, out, _ = shell.run("getprop ro.product.cpu.abi")
    info["cpu_arch"] = out.strip() if ok else "unknown"

    # CPU核心数 (使用 nproc --all 获取所有可能的CPU核心，而非仅在线核心)
    ok, out, _ = shell.run("nproc --all 2>/dev/null || nproc")
    if ok and out and out.strip().isdigit():
        info["cpu_cores"] = out.strip()
    else:
        # 备选: 扫描 /sys/devices/system/cpu/ 目录
        ok, out, _ = shell.run("ls -d /sys/devices/system/cpu/cpu[0-9]* 2>/dev/null | wc -l")
        info["cpu_cores"] = out.strip() if ok and out.strip().isdigit() else "unknown"

    # SoC平台
    info["soc_platform"] = _detect_soc()

    # GPU渲染器
    info["gpu_renderer"] = shell.get_prop("ro.hardware.egl") or \
        shell.read_node("/sys/class/kgsl/kgsl-3d0/gpu_model") or "unknown"

    # 内存
    ok, out, _ = shell.run("cat /proc/meminfo | grep MemTotal | awk '{print $2}'")
    if ok and out:
        total_kb = int(out.strip())
        info["total_ram"] = f"{total_kb // 1024} MB" if total_kb < 1048576 else f"{total_kb // 1048576} GB"

    # Root方式
    info["root_method"] = shell.root_method

    # SELinux状态
    ok, out, _ = shell.run("getenforce")
    info["selinux"] = out.strip() if ok else "unknown"

    return info


def _detect_rom() -> str:
    """检测ROM类型"""
    build = shell.get_prop("ro.build.version.incremental")
    display = shell.get_prop("ro.build.display.id")
    fingerprint = shell.get_prop("ro.build.fingerprint")

    combined = f"{build} {display} {fingerprint}".lower()
    roms = {
        "xiaomi": "MIUI/HyperOS",
        "hyperos": "HyperOS",
        "miui": "MIUI",
        "coloros": "ColorOS",
        "originos": "OriginOS",
        "flyme": "Flyme",
        "oneui": "OneUI",
        "emui": "EMUI",
        "magicos": "MagicOS",
        "lineage": "LineageOS",
        "pixel": "Pixel Experience",
    }
    for key, name in roms.items():
        if key in combined:
            return name
    return "AOSP/Stock"


def _detect_soc() -> str:
    """检测SoC平台"""
    from .config import SNAPDRAGON_DETECT_MAP
    
    hardware = shell.get_prop("ro.hardware.chipname") or shell.get_prop("ro.board.platform")
    soc_list = shell.get_prop("ro.soc.model") or ""
    cpuinfo = shell.run_raw("cat /proc/cpuinfo | grep Hardware | head -1")
    combined = f"{hardware} {soc_list} {cpuinfo}".lower()
    
    # 使用检测映射表匹配
    if "snapdragon" in combined or "qcom" in combined or "msm" in combined or "sm" in combined:
        for keywords, chip_name in SNAPDRAGON_DETECT_MAP:
            if any(kw in combined for kw in keywords):
                return f"Qualcomm Snapdragon {chip_name}"
        return "Qualcomm Snapdragon"
    elif "mediatek" in combined or "mt" in combined:
        return "MediaTek"
    elif "exynos" in combined:
        return "Samsung Exynos"
    elif "tensor" in combined:
        return "Google Tensor"
    return hardware or "Unknown"


def detect_cpu_cores() -> Dict[str, list]:
    """
    检测CPU大小核配置
    v1.0 适配: 骁龙8 Elite Oryon V2 (2×4.32GHz超大 + 6×3.53GHz大核)
              骁龙8 Gen 4/3/2 (1×3.3GHz超大 + 3/5×大 + 2/4×小)
    """
    cores = {"big": [], "middle": [], "little": []}

    # 扫描所有可能的CPU (0~15)
    max_cpus = 16
    # 先获取实际存在的CPU数量
    ok, out, _ = shell.run("ls -d /sys/devices/system/cpu/cpu[0-9]* 2>/dev/null | wc -l")
    if ok and out.strip().isdigit():
        max_cpus = min(int(out.strip()), 16)

    freq_list = []
    for i in range(max_cpus):
        max_freq_path = f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_max_freq"
        freq = shell.read_node_int(max_freq_path)
        if freq > 0:
            freq_list.append((i, freq))

    # 动态频率阈值: 按频率分组
    if not freq_list:
        return cores

    # 获取所有唯一频率值并排序
    unique_freqs = sorted(set(f for _, f in freq_list), reverse=True)

    # 根据频率分布自动分组
    # 骁龙8 Elite: 2核@4.32GHz + 6核@3.53GHz → 超大 + 大
    # 骁龙8 Gen 3: 1核@3.3GHz + 3核@3.15GHz + 2核@2.96GHz + 2核@2.27GHz
    for cpu_idx, freq in freq_list:
        if len(unique_freqs) >= 3:
            # 三档以上: 最高频→big, 中间→middle, 最低→little
            high_threshold = unique_freqs[0] * 0.85
            low_threshold = unique_freqs[-1] * 1.15
            if freq >= high_threshold:
                cores["big"].append(cpu_idx)
            elif freq <= low_threshold:
                cores["little"].append(cpu_idx)
            else:
                cores["middle"].append(cpu_idx)
        elif len(unique_freqs) == 2:
            # 两档: 高频→big, 低频→middle (骁龙8 Elite)
            mid = (unique_freqs[0] + unique_freqs[1]) / 2
            if freq > mid:
                cores["big"].append(cpu_idx)
            else:
                cores["middle"].append(cpu_idx)
        else:
            # 单档: 全部归big
            cores["big"].append(cpu_idx)

    return cores


def backup_config(name: str = "") -> str:
    """备份当前内核配置"""
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = name or f"backup_{timestamp}"
    backup_path = f"{BACKUP_DIR}/{backup_name}"

    shell.run(f"mkdir -p '{backup_path}'")

    # 备份CPU配置
    cpu_configs = []
    for i in range(8):
        gov = shell.read_node(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor")
        max_f = shell.read_node(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_max_freq")
        min_f = shell.read_node(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_min_freq")
        cpu_configs.append(f"cpu{i}: governor={gov} max={max_f} min={min_f}")

    shell.write_file(f"{backup_path}/cpu.conf", "\n".join(cpu_configs))

    # 备份GPU配置
    gpu_configs = []
    gpu_gov = shell.read_node("/sys/class/kgsl/kgsl-3d0/devfreq/governor")
    gpu_max = shell.read_node("/sys/class/kgsl/kgsl-3d0/max_gpuclk")
    gpu_min = shell.read_node("/sys/class/kgsl/kgsl-3d0/min_gpuclk")
    gpu_configs.extend([f"governor={gpu_gov}", f"max_gpuclk={gpu_max}", f"min_gpuclk={gpu_min}"])
    shell.write_file(f"{backup_path}/gpu.conf", "\n".join(gpu_configs))

    # 备份build.prop
    shell.run(f"cp /system/build.prop {backup_path}/build.prop.bak 2>/dev/null")
    shell.run(f"cp /vendor/build.prop {backup_path}/vendor_build.prop.bak 2>/dev/null")

    # 备份hosts
    shell.run(f"cp /system/etc/hosts {backup_path}/hosts.bak 2>/dev/null")

    # 备份温控配置
    shell.run(f"cp /vendor/etc/thermal-engine.conf {backup_path}/thermal.bak 2>/dev/null")
    shell.run(f"cp /system/etc/thermal-engine.conf {backup_path}/thermal_sys.bak 2>/dev/null")

    return backup_path


def log_event(level: str, module: str, message: str):
    """记录事件日志"""
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = f"{LOG_DIR}/toolbox_{datetime.now().strftime('%Y%m%d')}.log"
    shell.run(f"echo '[{timestamp}] [{level}] [{module}] {message}' >> {log_file}")
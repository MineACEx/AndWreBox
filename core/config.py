#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 - 全局配置与色彩主题
兼容: Android 16 / HyperOS 3 / MIUI / ColorOS / OriginOS / Flyme
"""

from rich.theme import Theme
from rich.style import Style
from rich.color import Color

# ============ 全局色彩主题 ============
# 深色模式为主，带渐变效果
CUSTOM_THEME = Theme({
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "info": "bold cyan",
    "highlight": "bold magenta",
    "title": "bold bright_cyan",
    "subtitle": "dim cyan",
    "panel.border": "cyan",
    "progress.remaining": "grey50",
    "progress.completed": "green",
    "table.header": "bold cyan",
})

# 渐变色定义 (用于 rich 面板边框)
GRADIENT_COLORS = [
    "cyan", "bright_cyan", "blue", "bright_blue",
    "magenta", "bright_magenta", "purple", "cyan"
]

# 日志级别色彩
LOG_COLORS = {
    "SUCCESS": "[bold green]✓[/]",
    "WARNING": "[bold yellow]⚠[/]",
    "ERROR": "[bold red]✗[/]",
    "INFO": "[bold cyan]ℹ[/]",
    "DEBUG": "[dim white]•[/]",
}

# ============ 设备信息缓存 ============
DEVICE_INFO = {
    "model": "",
    "manufacturer": "",
    "android_version": "",
    "sdk_version": "",
    "kernel_version": "",
    "cpu_arch": "",
    "cpu_cores": "",
    "soc_platform": "",
    "gpu_renderer": "",
    "total_ram": "",
    "rom_name": "",
    "root_method": "",
}

# 高通骁龙8 Gen系列专属路径
SNAPDRAGON_PATHS = {
    "cpu_freq": "/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq",
    "cpu_available_freq": "/sys/devices/system/cpu/cpu*/cpufreq/scaling_available_frequencies",
    "cpu_governor": "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor",
    "cpu_max_freq": "/sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq",
    "cpu_min_freq": "/sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq",
    "cpu_online": "/sys/devices/system/cpu/cpu*/online",
    "gpu_freq": "/sys/class/kgsl/kgsl-3d0/gpuclk",
    "gpu_max_freq": "/sys/class/kgsl/kgsl-3d0/max_gpuclk",
    "gpu_min_freq": "/sys/class/kgsl/kgsl-3d0/min_gpuclk",
    "gpu_governor": "/sys/class/kgsl/kgsl-3d0/devfreq/governor",
    "gpu_pwrlevel": "/sys/class/kgsl/kgsl-3d0/num_pwrlevels",
    "thermal_zone": "/sys/class/thermal/thermal_zone*/temp",
    "thermal_type": "/sys/class/thermal/thermal_zone*/type",
    "thermal_policy": "/sys/class/thermal/thermal_message/policy",
    "battery_capacity": "/sys/class/power_supply/battery/capacity",
    "battery_current": "/sys/class/power_supply/battery/current_now",
    "battery_voltage": "/sys/class/power_supply/battery/voltage_now",
    "battery_temp": "/sys/class/power_supply/battery/temp",
}

# 温控预设配置
THERMAL_PROFILES = {
    "daily": {  # 日常省电
        "cpu_throttle": 65,
        "gpu_throttle": 60,
        "battery_throttle": 42,
        "description": "日常省电模式 - 温和温控，延长续航"
    },
    "balanced": {  # 均衡
        "cpu_throttle": 75,
        "gpu_throttle": 70,
        "battery_throttle": 45,
        "description": "均衡模式 - 性能与温度平衡"
    },
    "gaming": {  # 游戏狂暴
        "cpu_throttle": 90,
        "gpu_throttle": 85,
        "battery_throttle": 48,
        "description": "游戏狂暴模式 - 拉高温控阈值，释放满血性能"
    },
}

# CPU调度器预设
CPU_GOVERNOR_PROFILES = {
    "schedutil": "骁龙8 Gen系列推荐 - 智能动态调度，能效比最优",
    "performance": "性能优先 - 锁定最高频率，功耗极高",
    "ondemand": "按需调度 - 负载高时提频，空闲时降频",
    "conservative": "保守调度 - 缓慢提频，极致省电",
    "powersave": "省电优先 - 锁定最低频率，性能最低",
}

# 快捷模式预设
QUICK_MODES = {
    "performance": {
        "name": "一键高性能模式",
        "cpu_gov": "performance",
        "cpu_min": "high",
        "gpu_gov": "performance",
        "thermal": "gaming",
        "oom": "aggressive",
    },
    "powersave": {
        "name": "一键省电极限模式",
        "cpu_gov": "powersave",
        "cpu_min": "low",
        "gpu_gov": "powersave",
        "thermal": "daily",
        "oom": "light",
    },
    "balanced": {
        "name": "智能均衡模式",
        "cpu_gov": "schedutil",
        "cpu_min": "mid",
        "gpu_gov": "simple_ondemand",
        "thermal": "balanced",
        "oom": "medium",
    },
}

# 数据目录（统一由 core/paths.py 管理，此处保留兼容导出）
from .paths import DATA_DIR, AUTH_DIR, CONFIG_DIR, BACKUP_DIR, LOG_DIR, TMP_DIR
from .paths import get_module_output_dir as _get_out
CONFIG_DIR = DATA_DIR
OUTPUT_DIR = _get_out()

# ============ 骁龙芯片完整适配列表 ============
# 每代芯片的专属参数
SNAPDRAGON_CHIPS = {
    # 2025-2026 旗舰
    "8 Elite": {  # 骁龙8 Elite (SM8750) - 第二代Oryon CPU
        "codename": "SM8750",
        "cpu_max_freq_big": 4320,      # 4.32GHz Oryon超大核
        "cpu_max_freq_mid": 3530,      # 3.53GHz Oryon性能核
        "cpu_cores": 8,                # 2+6
        "gpu": "Adreno 830",
        "gpu_max_freq": 1100,          # MHz
        "process": "3nm TSMC N3E",
        "year": 2025,
    },
    "8 Gen 5 Elite": {  # 骁龙8 Gen 5 Elite (SM8850) - 第三代Oryon
        "codename": "SM8850",
        "cpu_max_freq_big": 4500,      # 预估
        "cpu_max_freq_mid": 3700,
        "cpu_cores": 8,
        "gpu": "Adreno 840",
        "gpu_max_freq": 1200,
        "process": "3nm TSMC N3P",
        "year": 2026,
    },
    # 2024 旗舰
    "8 Gen 4": {  # 骁龙8 Gen 4 (SM8750) - 初代Oryon
        "codename": "SM8750",
        "cpu_max_freq_big": 4260,      # 4.26GHz Oryon超大核
        "cpu_max_freq_mid": 2800,      # 2.8GHz Oryon性能核
        "cpu_cores": 8,                # 2+6
        "gpu": "Adreno 830",
        "gpu_max_freq": 1100,
        "process": "3nm TSMC N3E",
        "year": 2024,
    },
    "8s Gen 4": {  # 骁龙8s Gen 4
        "codename": "SM8735",
        "cpu_max_freq_big": 3200,
        "cpu_max_freq_mid": 2800,
        "cpu_cores": 8,
        "gpu": "Adreno 825",
        "gpu_max_freq": 900,
        "process": "4nm TSMC",
        "year": 2025,
    },
    # 2023 旗舰
    "8 Gen 3": {  # 骁龙8 Gen 3 (SM8650)
        "codename": "SM8650",
        "cpu_max_freq_big": 3300,      # 3.3GHz Cortex-X4
        "cpu_max_freq_mid": 3200,      # 3.2GHz Cortex-A720
        "cpu_max_freq_little": 2300,   # 2.3GHz Cortex-A520
        "cpu_cores": 8,                # 1+3+2+2
        "gpu": "Adreno 750",
        "gpu_max_freq": 903,
        "process": "4nm TSMC",
        "year": 2023,
    },
    "8s Gen 3": {  # 骁龙8s Gen 3 (SM8635)
        "codename": "SM8635",
        "cpu_max_freq_big": 3000,
        "cpu_max_freq_mid": 2800,
        "cpu_max_freq_little": 2000,
        "cpu_cores": 8,
        "gpu": "Adreno 735",
        "gpu_max_freq": 800,
        "process": "4nm TSMC",
        "year": 2024,
    },
    # 2022 旗舰
    "8 Gen 2": {
        "codename": "SM8550",
        "cpu_max_freq_big": 3200,
        "cpu_max_freq_mid": 2800,
        "cpu_max_freq_little": 2000,
        "cpu_cores": 8,
        "gpu": "Adreno 740",
        "gpu_max_freq": 680,
        "process": "4nm TSMC",
        "year": 2022,
    },
    "8+ Gen 1": {
        "codename": "SM8475",
        "cpu_max_freq_big": 3200,
        "cpu_max_freq_mid": 2750,
        "cpu_max_freq_little": 2000,
        "cpu_cores": 8,
        "gpu": "Adreno 730",
        "gpu_max_freq": 900,
        "process": "4nm TSMC",
        "year": 2022,
    },
    "8 Gen 1": {
        "codename": "SM8450",
        "cpu_max_freq_big": 3000,
        "cpu_max_freq_mid": 2500,
        "cpu_max_freq_little": 1800,
        "cpu_cores": 8,
        "gpu": "Adreno 730",
        "gpu_max_freq": 818,
        "process": "4nm Samsung",
        "year": 2021,
    },
    # 中高端芯片
    "7+ Gen 3": {
        "codename": "SM7675",
        "cpu_max_freq_big": 2800,
        "cpu_max_freq_mid": 2600,
        "cpu_max_freq_little": 1900,
        "cpu_cores": 8,
        "gpu": "Adreno 732",
        "gpu_max_freq": 700,
        "process": "4nm TSMC",
        "year": 2024,
    },
    "7 Gen 3": {
        "codename": "SM7550",
        "cpu_max_freq_big": 2630,
        "cpu_max_freq_mid": 2400,
        "cpu_max_freq_little": 1800,
        "cpu_cores": 8,
        "gpu": "Adreno 720",
        "gpu_max_freq": 600,
        "process": "4nm TSMC",
        "year": 2023,
    },
    "888": {
        "codename": "SM8350",
        "cpu_max_freq_big": 2840,
        "cpu_max_freq_mid": 2420,
        "cpu_max_freq_little": 1800,
        "cpu_cores": 8,
        "gpu": "Adreno 660",
        "gpu_max_freq": 840,
        "process": "5nm Samsung",
        "year": 2020,
    },
    "888+": {
        "codename": "SM8350-AC",
        "cpu_max_freq_big": 3000,
        "cpu_max_freq_mid": 2420,
        "cpu_max_freq_little": 1800,
        "cpu_cores": 8,
        "gpu": "Adreno 660",
        "gpu_max_freq": 900,
        "process": "5nm Samsung",
        "year": 2021,
    },
    "870": {
        "codename": "SM8250-AC",
        "cpu_max_freq_big": 3200,
        "cpu_max_freq_mid": 2420,
        "cpu_max_freq_little": 1800,
        "cpu_cores": 8,
        "gpu": "Adreno 650",
        "gpu_max_freq": 670,
        "process": "7nm TSMC",
        "year": 2021,
    },
    "865": {
        "codename": "SM8250",
        "cpu_max_freq_big": 2840,
        "cpu_max_freq_mid": 2420,
        "cpu_max_freq_little": 1800,
        "cpu_cores": 8,
        "gpu": "Adreno 650",
        "gpu_max_freq": 587,
        "process": "7nm TSMC",
        "year": 2019,
    },
    "865+": {
        "codename": "SM8250-AB",
        "cpu_max_freq_big": 3100,
        "cpu_max_freq_mid": 2420,
        "cpu_max_freq_little": 1800,
        "cpu_cores": 8,
        "gpu": "Adreno 650",
        "gpu_max_freq": 670,
        "process": "7nm TSMC",
        "year": 2020,
    },
    "855": {
        "codename": "SM8150",
        "cpu_max_freq_big": 2840,
        "cpu_max_freq_mid": 2420,
        "cpu_max_freq_little": 1780,
        "cpu_cores": 8,
        "gpu": "Adreno 640",
        "gpu_max_freq": 585,
        "process": "7nm TSMC",
        "year": 2018,
    },
    "855+": {
        "codename": "SM8150-AC",
        "cpu_max_freq_big": 2960,
        "cpu_max_freq_mid": 2420,
        "cpu_max_freq_little": 1780,
        "cpu_cores": 8,
        "gpu": "Adreno 640",
        "gpu_max_freq": 675,
        "process": "7nm TSMC",
        "year": 2019,
    },
    "845": {
        "codename": "SDM845",
        "cpu_max_freq_big": 2800,
        "cpu_max_freq_little": 1760,
        "cpu_cores": 8,
        "gpu": "Adreno 630",
        "gpu_max_freq": 710,
        "process": "10nm Samsung",
        "year": 2017,
    },
    # 骁龙8 Elite for Galaxy 特别版
    "8 Elite for Galaxy": {
        "codename": "SM8750-AB",
        "cpu_max_freq_big": 4470,      # 超频版
        "cpu_max_freq_mid": 3530,
        "cpu_cores": 8,
        "gpu": "Adreno 830",
        "gpu_max_freq": 1150,
        "process": "3nm TSMC N3E",
        "year": 2025,
    },
}

# ============ 骁龙芯片检测关键词 ============
# 用于从设备信息中匹配芯片型号
SNAPDRAGON_DETECT_MAP = [
    # (关键词列表, 芯片名称)
    (["sm8750", "8 elite", "sun"], "8 Elite"),
    (["sm8850", "8 gen 5"], "8 Gen 5 Elite"),
    (["sm8735", "8s gen 4"], "8s Gen 4"),
    (["sm8650", "8 gen 3", "pineapple"], "8 Gen 3"),
    (["sm8635", "8s gen 3", "cliffs"], "8s Gen 3"),
    (["sm8550", "8 gen 2", "kalama"], "8 Gen 2"),
    (["sm8475", "8+ gen 1", "cape"], "8+ Gen 1"),
    (["sm8450", "8 gen 1", "taro"], "8 Gen 1"),
    (["sm7675", "7+ gen 3"], "7+ Gen 3"),
    (["sm7550", "7 gen 3"], "7 Gen 3"),
    (["sm8350-ac", "sm8350ac", "888+", "lahaina-ac"], "888+"),
    (["sm8350", "888", "lahaina"], "888"),
    (["sm8250-ac", "sm8250ac", "870"], "870"),
    (["sm8250-ab", "sm8250ab", "865+"], "865+"),
    (["sm8250", "865", "kona"], "865"),
    (["sm8150-ac", "sm8150ac", "855+"], "855+"),
    (["sm8150", "855", "msmnile"], "855"),
    (["sdm845", "845"], "845"),
]

# APP版本
VERSION = "v1.0"
BUILD_DATE = "2026-06-17"
AUTHOR = "AndWreBox Team"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from core.shell import shell
from core.i18n import T
from core.animations import (
    console, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)
from core.utils import log_event

# 伪装备份目录
SPOOF_BACKUP_DIR = "/sdcard/AndroidRootToolbox/spoof_backup"

# ============================================================
# 设备型号预设模板库
# 每个模板包含: brand, model_name, model_code, soc, props
# props 包含完整的 ro.product.* 和 ro.build.* 属性
# ============================================================
DEVICE_TEMPLATES = {
    "snapdragon_8_elite": {
        "category_name": "Snapdragon 8 Elite / Gen 5 系列 (2025-2026)",
        "devices": [
            {
                "brand": "Samsung",
                "model_name": "Galaxy S25 Ultra",
                "model_code": "SM-S938B",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "SM-S938B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "e3sxx",
                    "ro.product.device": "e3s",
                    "ro.product.board": "e3s",
                    "ro.build.fingerprint": "samsung/e3sxx/e3s:15/AP3A.240905.015.A2/S938BXXU1AXK5:user/release-keys",
                    "ro.build.description": "e3sxx-user 15 AP3A.240905.015.A2 S938BXXU1AXK5 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.S938BXXU1AXK5",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy S25+",
                "model_code": "SM-S936B",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "SM-S936B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "e2sxx",
                    "ro.product.device": "e2s",
                    "ro.product.board": "e2s",
                    "ro.build.fingerprint": "samsung/e2sxx/e2s:15/AP3A.240905.015.A2/S936BXXU1AXK5:user/release-keys",
                    "ro.build.description": "e2sxx-user 15 AP3A.240905.015.A2 S936BXXU1AXK5 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.S936BXXU1AXK5",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy S25",
                "model_code": "SM-S931B",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "SM-S931B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "e1sxx",
                    "ro.product.device": "e1s",
                    "ro.product.board": "e1s",
                    "ro.build.fingerprint": "samsung/e1sxx/e1s:15/AP3A.240905.015.A2/S931BXXU1AXK5:user/release-keys",
                    "ro.build.description": "e1sxx-user 15 AP3A.240905.015.A2 S931BXXU1AXK5 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.S931BXXU1AXK5",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy Z Fold 7",
                "model_code": "SM-F966B",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "SM-F966B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "q7sxx",
                    "ro.product.device": "q7s",
                    "ro.product.board": "q7s",
                    "ro.build.fingerprint": "samsung/q7sxx/q7s:15/AP3A.240905.015.A2/F966BXXU1AXK5:user/release-keys",
                    "ro.build.description": "q7sxx-user 15 AP3A.240905.015.A2 F966BXXU1AXK5 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.F966BXXU1AXK5",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy Z Flip 7",
                "model_code": "SM-F741B",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "SM-F741B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "b7sxx",
                    "ro.product.device": "b7s",
                    "ro.product.board": "b7s",
                    "ro.build.fingerprint": "samsung/b7sxx/b7s:15/AP3A.240905.015.A2/F741BXXU1AXK5:user/release-keys",
                    "ro.build.description": "b7sxx-user 15 AP3A.240905.015.A2 F741BXXU1AXK5 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.F741BXXU1AXK5",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 15 Ultra",
                "model_code": "25010PN30G",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "25010PN30G",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "aurora",
                    "ro.product.device": "aurora",
                    "ro.product.board": "aurora",
                    "ro.build.fingerprint": "Xiaomi/aurora/aurora:15/AP3A.240905.015.A2/V816.0.6.0.ULAMIXM:user/release-keys",
                    "ro.build.description": "aurora-user 15 AP3A.240905.015.A2 V816.0.6.0.ULAMIXM release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.V816.0.6.0.ULAMIXM",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 15 Pro",
                "model_code": "2410DPN6CC",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "2410DPN6CC",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "haotian",
                    "ro.product.device": "haotian",
                    "ro.product.board": "haotian",
                    "ro.build.fingerprint": "Xiaomi/haotian/haotian:15/AP3A.240905.015.A2/V816.0.3.0.ULBCNXM:user/release-keys",
                    "ro.build.description": "haotian-user 15 AP3A.240905.015.A2 V816.0.3.0.ULBCNXM release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.V816.0.3.0.ULBCNXM",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 15",
                "model_code": "24129PN74C",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "24129PN74C",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "dada",
                    "ro.product.device": "dada",
                    "ro.product.board": "dada",
                    "ro.build.fingerprint": "Xiaomi/dada/dada:15/AP3A.240905.015.A2/V816.0.1.0.ULCCNXM:user/release-keys",
                    "ro.build.description": "dada-user 15 AP3A.240905.015.A2 V816.0.1.0.ULCCNXM release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.V816.0.1.0.ULCCNXM",
                }
            },
            {
                "brand": "OnePlus",
                "model_name": "OnePlus 13",
                "model_code": "CPH2653",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "CPH2653",
                    "ro.product.manufacturer": "OnePlus",
                    "ro.product.brand": "OnePlus",
                    "ro.product.name": "OP594DL1",
                    "ro.product.device": "OP594DL1",
                    "ro.product.board": "OP594DL1",
                    "ro.build.fingerprint": "OnePlus/OP594DL1/OP594DL1:15/AP3A.240905.015.A2/CPH2653_15.0.0.400:user/release-keys",
                    "ro.build.description": "OP594DL1-user 15 AP3A.240905.015.A2 CPH2653_15.0.0.400 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.CPH2653_15.0.0.400",
                }
            },
            {
                "brand": "OnePlus",
                "model_name": "OnePlus 13R",
                "model_code": "CPH2691",
                "soc": "Snapdragon 8 Gen 4",
                "props": {
                    "ro.product.model": "CPH2691",
                    "ro.product.manufacturer": "OnePlus",
                    "ro.product.brand": "OnePlus",
                    "ro.product.name": "OP596DL1",
                    "ro.product.device": "OP596DL1",
                    "ro.product.board": "OP596DL1",
                    "ro.build.fingerprint": "OnePlus/OP596DL1/OP596DL1:15/AP3A.240905.015.A2/CPH2691_15.0.0.310:user/release-keys",
                    "ro.build.description": "OP596DL1-user 15 AP3A.240905.015.A2 CPH2691_15.0.0.310 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.CPH2691_15.0.0.310",
                }
            },
            {
                "brand": "OPPO",
                "model_name": "Find X8 Ultra",
                "model_code": "CPH2771",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "CPH2771",
                    "ro.product.manufacturer": "OPPO",
                    "ro.product.brand": "OPPO",
                    "ro.product.name": "OP5B1FL1",
                    "ro.product.device": "OP5B1FL1",
                    "ro.product.board": "OP5B1FL1",
                    "ro.build.fingerprint": "OPPO/OP5B1FL1/OP5B1FL1:15/AP3A.240905.015.A2/CPH2771_15.0.0.410:user/release-keys",
                    "ro.build.description": "OP5B1FL1-user 15 AP3A.240905.015.A2 CPH2771_15.0.0.410 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.CPH2771_15.0.0.410",
                }
            },
            {
                "brand": "OPPO",
                "model_name": "Find X8 Pro",
                "model_code": "CPH2755",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "CPH2755",
                    "ro.product.manufacturer": "OPPO",
                    "ro.product.brand": "OPPO",
                    "ro.product.name": "OP5A9FL1",
                    "ro.product.device": "OP5A9FL1",
                    "ro.product.board": "OP5A9FL1",
                    "ro.build.fingerprint": "OPPO/OP5A9FL1/OP5A9FL1:15/AP3A.240905.015.A2/CPH2755_15.0.0.350:user/release-keys",
                    "ro.build.description": "OP5A9FL1-user 15 AP3A.240905.015.A2 CPH2755_15.0.0.350 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.CPH2755_15.0.0.350",
                }
            },
            {
                "brand": "vivo",
                "model_name": "X200 Ultra",
                "model_code": "V2425A",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "V2425A",
                    "ro.product.manufacturer": "vivo",
                    "ro.product.brand": "vivo",
                    "ro.product.name": "PD2425",
                    "ro.product.device": "PD2425",
                    "ro.product.board": "PD2425",
                    "ro.build.fingerprint": "vivo/PD2425/PD2425:15/AP3A.240905.015.A2/V2425A_15.0.18.10:user/release-keys",
                    "ro.build.description": "PD2425-user 15 AP3A.240905.015.A2 V2425A_15.0.18.10 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.V2425A_15.0.18.10",
                }
            },
            {
                "brand": "vivo",
                "model_name": "X200 Pro",
                "model_code": "V2413A",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "V2413A",
                    "ro.product.manufacturer": "vivo",
                    "ro.product.brand": "vivo",
                    "ro.product.name": "PD2413",
                    "ro.product.device": "PD2413",
                    "ro.product.board": "PD2413",
                    "ro.build.fingerprint": "vivo/PD2413/PD2413:15/AP3A.240905.015.A2/V2413A_15.0.20.5:user/release-keys",
                    "ro.build.description": "PD2413-user 15 AP3A.240905.015.A2 V2413A_15.0.20.5 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.V2413A_15.0.20.5",
                }
            },
            {
                "brand": "iQOO",
                "model_name": "iQOO 13",
                "model_code": "I2401",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "I2401",
                    "ro.product.manufacturer": "vivo",
                    "ro.product.brand": "iQOO",
                    "ro.product.name": "PD2401",
                    "ro.product.device": "PD2401",
                    "ro.product.board": "PD2401",
                    "ro.build.fingerprint": "iQOO/PD2401/PD2401:15/AP3A.240905.015.A2/I2401_15.0.12.8:user/release-keys",
                    "ro.build.description": "PD2401-user 15 AP3A.240905.015.A2 I2401_15.0.12.8 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.I2401_15.0.12.8",
                }
            },
            {
                "brand": "Realme",
                "model_name": "GT 8 Pro",
                "model_code": "RMX5090",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "RMX5090",
                    "ro.product.manufacturer": "realme",
                    "ro.product.brand": "realme",
                    "ro.product.name": "RE5C9FL1",
                    "ro.product.device": "RE5C9FL1",
                    "ro.product.board": "RE5C9FL1",
                    "ro.build.fingerprint": "realme/RE5C9FL1/RE5C9FL1:15/AP3A.240905.015.A2/RMX5090_15.0.0.510:user/release-keys",
                    "ro.build.description": "RE5C9FL1-user 15 AP3A.240905.015.A2 RMX5090_15.0.0.510 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.RMX5090_15.0.0.510",
                }
            },
            {
                "brand": "ASUS",
                "model_name": "ROG Phone 9",
                "model_code": "AI2501",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "AI2501",
                    "ro.product.manufacturer": "asus",
                    "ro.product.brand": "asus",
                    "ro.product.name": "ASUS_AI2501",
                    "ro.product.device": "ASUS_AI2501",
                    "ro.product.board": "ASUS_AI2501",
                    "ro.build.fingerprint": "asus/ASUS_AI2501/ASUS_AI2501:15/AP3A.240905.015.A2/AI2501_35.1010.1010.0:user/release-keys",
                    "ro.build.description": "ASUS_AI2501-user 15 AP3A.240905.015.A2 AI2501_35.1010.1010.0 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.AI2501_35.1010.1010.0",
                }
            },
            {
                "brand": "Red Magic",
                "model_name": "Red Magic 10 Pro",
                "model_code": "NX789J",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "NX789J",
                    "ro.product.manufacturer": "nubia",
                    "ro.product.brand": "nubia",
                    "ro.product.name": "NX789J",
                    "ro.product.device": "NX789J",
                    "ro.product.board": "NX789J",
                    "ro.build.fingerprint": "nubia/NX789J/NX789J:15/AP3A.240905.015.A2/NX789J_V3.10:user/release-keys",
                    "ro.build.description": "NX789J-user 15 AP3A.240905.015.A2 NX789J_V3.10 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.NX789J_V3.10",
                }
            },
            {
                "brand": "Honor",
                "model_name": "Magic 7 Pro",
                "model_code": "BVL-AN00",
                "soc": "Snapdragon 8 Elite",
                "props": {
                    "ro.product.model": "BVL-AN00",
                    "ro.product.manufacturer": "HONOR",
                    "ro.product.brand": "honor",
                    "ro.product.name": "BVL-AN00",
                    "ro.product.device": "HNBVL-AN00",
                    "ro.product.board": "HNBVL-AN00",
                    "ro.build.fingerprint": "honor/HNBVL-AN00/HNBVL-AN00:15/AP3A.240905.015.A2/BVL-AN00_9.0.0.160:user/release-keys",
                    "ro.build.description": "HNBVL-AN00-user 15 AP3A.240905.015.A2 BVL-AN00_9.0.0.160 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.BVL-AN00_9.0.0.160",
                }
            },
            {
                "brand": "Google",
                "model_name": "Pixel 10 Pro",
                "model_code": "G4V4A",
                "soc": "Tensor G5",
                "props": {
                    "ro.product.model": "Pixel 10 Pro",
                    "ro.product.manufacturer": "Google",
                    "ro.product.brand": "google",
                    "ro.product.name": "raven",
                    "ro.product.device": "raven",
                    "ro.product.board": "raven",
                    "ro.build.fingerprint": "google/raven/raven:15/AP3A.240905.015.A2/12051.2000.16:user/release-keys",
                    "ro.build.description": "raven-user 15 AP3A.240905.015.A2 12051.2000.16 release-keys",
                    "ro.build.display.id": "AP3A.240905.015.A2.12051.2000.16",
                }
            },
        ]
    },
    "snapdragon_8_gen3": {
        "category_name": "Snapdragon 8 Gen 3 系列 (2024)",
        "devices": [
            {
                "brand": "Samsung",
                "model_name": "Galaxy S24 Ultra",
                "model_code": "SM-S928B",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "SM-S928B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "e3qxx",
                    "ro.product.device": "e3q",
                    "ro.product.board": "e3q",
                    "ro.build.fingerprint": "samsung/e3qxx/e3q:14/UP1A.231005.007/S928BXXU1AXK4:user/release-keys",
                    "ro.build.description": "e3qxx-user 14 UP1A.231005.007 S928BXXU1AXK4 release-keys",
                    "ro.build.display.id": "UP1A.231005.007.S928BXXU1AXK4",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy S24+",
                "model_code": "SM-S926B",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "SM-S926B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "e2qxx",
                    "ro.product.device": "e2q",
                    "ro.product.board": "e2q",
                    "ro.build.fingerprint": "samsung/e2qxx/e2q:14/UP1A.231005.007/S926BXXU1AXK4:user/release-keys",
                    "ro.build.description": "e2qxx-user 14 UP1A.231005.007 S926BXXU1AXK4 release-keys",
                    "ro.build.display.id": "UP1A.231005.007.S926BXXU1AXK4",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy S24",
                "model_code": "SM-S921B",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "SM-S921B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "e1qxx",
                    "ro.product.device": "e1q",
                    "ro.product.board": "e1q",
                    "ro.build.fingerprint": "samsung/e1qxx/e1q:14/UP1A.231005.007/S921BXXU1AXK4:user/release-keys",
                    "ro.build.description": "e1qxx-user 14 UP1A.231005.007 S921BXXU1AXK4 release-keys",
                    "ro.build.display.id": "UP1A.231005.007.S921BXXU1AXK4",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 14 Ultra",
                "model_code": "24030PN60G",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "24030PN60G",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "aurora",
                    "ro.product.device": "aurora",
                    "ro.product.board": "aurora",
                    "ro.build.fingerprint": "Xiaomi/aurora/aurora:14/UP1A.231005.007/V816.0.18.0.ULAMIXM:user/release-keys",
                    "ro.build.description": "aurora-user 14 UP1A.231005.007 V816.0.18.0.ULAMIXM release-keys",
                    "ro.build.display.id": "UP1A.231005.007.V816.0.18.0.ULAMIXM",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 14 Pro",
                "model_code": "2311DRK48C",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "2311DRK48C",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "shennong",
                    "ro.product.device": "shennong",
                    "ro.product.board": "shennong",
                    "ro.build.fingerprint": "Xiaomi/shennong/shennong:14/UP1A.231005.007/V816.0.17.0.ULBCNXM:user/release-keys",
                    "ro.build.description": "shennong-user 14 UP1A.231005.007 V816.0.17.0.ULBCNXM release-keys",
                    "ro.build.display.id": "UP1A.231005.007.V816.0.17.0.ULBCNXM",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 14",
                "model_code": "23127PN0CC",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "23127PN0CC",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "houji",
                    "ro.product.device": "houji",
                    "ro.product.board": "houji",
                    "ro.build.fingerprint": "Xiaomi/houji/houji:14/UP1A.231005.007/V816.0.13.0.ULCCNXM:user/release-keys",
                    "ro.build.description": "houji-user 14 UP1A.231005.007 V816.0.13.0.ULCCNXM release-keys",
                    "ro.build.display.id": "UP1A.231005.007.V816.0.13.0.ULCCNXM",
                }
            },
            {
                "brand": "OnePlus",
                "model_name": "OnePlus 12",
                "model_code": "CPH2581",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "CPH2581",
                    "ro.product.manufacturer": "OnePlus",
                    "ro.product.brand": "OnePlus",
                    "ro.product.name": "OP5961L1",
                    "ro.product.device": "OP5961L1",
                    "ro.product.board": "OP5961L1",
                    "ro.build.fingerprint": "OnePlus/OP5961L1/OP5961L1:14/UP1A.231005.007/CPH2581_14.0.0.850:user/release-keys",
                    "ro.build.description": "OP5961L1-user 14 UP1A.231005.007 CPH2581_14.0.0.850 release-keys",
                    "ro.build.display.id": "UP1A.231005.007.CPH2581_14.0.0.850",
                }
            },
            {
                "brand": "OPPO",
                "model_name": "Find X7 Ultra",
                "model_code": "PHY110",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "PHY110",
                    "ro.product.manufacturer": "OPPO",
                    "ro.product.brand": "OPPO",
                    "ro.product.name": "OP5B1FL1",
                    "ro.product.device": "OP5B1FL1",
                    "ro.product.board": "OP5B1FL1",
                    "ro.build.fingerprint": "OPPO/OP5B1FL1/OP5B1FL1:14/UP1A.231005.007/PHY110_14.0.0.830:user/release-keys",
                    "ro.build.description": "OP5B1FL1-user 14 UP1A.231005.007 PHY110_14.0.0.830 release-keys",
                    "ro.build.display.id": "UP1A.231005.007.PHY110_14.0.0.830",
                }
            },
            {
                "brand": "vivo",
                "model_name": "X100 Ultra",
                "model_code": "V2366A",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "V2366A",
                    "ro.product.manufacturer": "vivo",
                    "ro.product.brand": "vivo",
                    "ro.product.name": "PD2366",
                    "ro.product.device": "PD2366",
                    "ro.product.board": "PD2366",
                    "ro.build.fingerprint": "vivo/PD2366/PD2366:14/UP1A.231005.007/V2366A_14.0.16.3:user/release-keys",
                    "ro.build.description": "PD2366-user 14 UP1A.231005.007 V2366A_14.0.16.3 release-keys",
                    "ro.build.display.id": "UP1A.231005.007.V2366A_14.0.16.3",
                }
            },
            {
                "brand": "Realme",
                "model_name": "GT 5 Pro",
                "model_code": "RMX3888",
                "soc": "Snapdragon 8 Gen 3",
                "props": {
                    "ro.product.model": "RMX3888",
                    "ro.product.manufacturer": "realme",
                    "ro.product.brand": "realme",
                    "ro.product.name": "RE5B9FL1",
                    "ro.product.device": "RE5B9FL1",
                    "ro.product.board": "RE5B9FL1",
                    "ro.build.fingerprint": "realme/RE5B9FL1/RE5B9FL1:14/UP1A.231005.007/RMX3888_14.0.0.810:user/release-keys",
                    "ro.build.description": "RE5B9FL1-user 14 UP1A.231005.007 RMX3888_14.0.0.810 release-keys",
                    "ro.build.display.id": "UP1A.231005.007.RMX3888_14.0.0.810",
                }
            },
        ]
    },
    "snapdragon_8_gen2": {
        "category_name": "Snapdragon 8 Gen 2 系列 (2023)",
        "devices": [
            {
                "brand": "Samsung",
                "model_name": "Galaxy S23 Ultra",
                "model_code": "SM-S918B",
                "soc": "Snapdragon 8 Gen 2",
                "props": {
                    "ro.product.model": "SM-S918B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "dm3qxx",
                    "ro.product.device": "dm3q",
                    "ro.product.board": "dm3q",
                    "ro.build.fingerprint": "samsung/dm3qxx/dm3q:13/TP1A.220624.014/S918BXXU1AWE3:user/release-keys",
                    "ro.build.description": "dm3qxx-user 13 TP1A.220624.014 S918BXXU1AWE3 release-keys",
                    "ro.build.display.id": "TP1A.220624.014.S918BXXU1AWE3",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy S23+",
                "model_code": "SM-S916B",
                "soc": "Snapdragon 8 Gen 2",
                "props": {
                    "ro.product.model": "SM-S916B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "dm2qxx",
                    "ro.product.device": "dm2q",
                    "ro.product.board": "dm2q",
                    "ro.build.fingerprint": "samsung/dm2qxx/dm2q:13/TP1A.220624.014/S916BXXU1AWE3:user/release-keys",
                    "ro.build.description": "dm2qxx-user 13 TP1A.220624.014 S916BXXU1AWE3 release-keys",
                    "ro.build.display.id": "TP1A.220624.014.S916BXXU1AWE3",
                }
            },
            {
                "brand": "Samsung",
                "model_name": "Galaxy S23",
                "model_code": "SM-S911B",
                "soc": "Snapdragon 8 Gen 2",
                "props": {
                    "ro.product.model": "SM-S911B",
                    "ro.product.manufacturer": "samsung",
                    "ro.product.brand": "samsung",
                    "ro.product.name": "dm1qxx",
                    "ro.product.device": "dm1q",
                    "ro.product.board": "dm1q",
                    "ro.build.fingerprint": "samsung/dm1qxx/dm1q:13/TP1A.220624.014/S911BXXU1AWE3:user/release-keys",
                    "ro.build.description": "dm1qxx-user 13 TP1A.220624.014 S911BXXU1AWE3 release-keys",
                    "ro.build.display.id": "TP1A.220624.014.S911BXXU1AWE3",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 13 Ultra",
                "model_code": "2304FPN6DC",
                "soc": "Snapdragon 8 Gen 2",
                "props": {
                    "ro.product.model": "2304FPN6DC",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "ishtar",
                    "ro.product.device": "ishtar",
                    "ro.product.board": "ishtar",
                    "ro.build.fingerprint": "Xiaomi/ishtar/ishtar:13/TP1A.220624.014/V14.0.9.0.TMAMIXM:user/release-keys",
                    "ro.build.description": "ishtar-user 13 TP1A.220624.014 V14.0.9.0.TMAMIXM release-keys",
                    "ro.build.display.id": "TP1A.220624.014.V14.0.9.0.TMAMIXM",
                }
            },
            {
                "brand": "Xiaomi",
                "model_name": "Xiaomi 13 Pro",
                "model_code": "2210132G",
                "soc": "Snapdragon 8 Gen 2",
                "props": {
                    "ro.product.model": "2210132G",
                    "ro.product.manufacturer": "Xiaomi",
                    "ro.product.brand": "Xiaomi",
                    "ro.product.name": "nuwa",
                    "ro.product.device": "nuwa",
                    "ro.product.board": "nuwa",
                    "ro.build.fingerprint": "Xiaomi/nuwa/nuwa:13/TP1A.220624.014/V14.0.11.0.TMBMIXM:user/release-keys",
                    "ro.build.description": "nuwa-user 13 TP1A.220624.014 V14.0.11.0.TMBMIXM release-keys",
                    "ro.build.display.id": "TP1A.220624.014.V14.0.11.0.TMBMIXM",
                }
            },
            {
                "brand": "OnePlus",
                "model_name": "OnePlus 11",
                "model_code": "CPH2449",
                "soc": "Snapdragon 8 Gen 2",
                "props": {
                    "ro.product.model": "CPH2449",
                    "ro.product.manufacturer": "OnePlus",
                    "ro.product.brand": "OnePlus",
                    "ro.product.name": "OP594DL1",
                    "ro.product.device": "OP594DL1",
                    "ro.product.board": "OP594DL1",
                    "ro.build.fingerprint": "OnePlus/OP594DL1/OP594DL1:13/TP1A.220624.014/CPH2449_13.1.0.501:user/release-keys",
                    "ro.build.description": "OP594DL1-user 13 TP1A.220624.014 CPH2449_13.1.0.501 release-keys",
                    "ro.build.display.id": "TP1A.220624.014.CPH2449_13.1.0.501",
                }
            },
        ]
    },
}


class SpoofingCenter:
    """设备伪装中心"""

    def __init__(self):
        shell.mkdir(SPOOF_BACKUP_DIR)
        self._backup_current()

    def _backup_current(self):
        """备份当前属性值"""
        props = [
            "ro.product.model", "ro.product.manufacturer", "ro.product.brand",
            "ro.product.name", "ro.product.device", "ro.product.board",
            "ro.build.product", "ro.build.fingerprint", "ro.build.description",
            "ro.build.display.id", "ro.hardware.egl", "ro.hardware",
            "ro.board.platform", "ro.chipname",
        ]
        backup = {}
        for prop in props:
            backup[prop] = shell.get_prop(prop)
        # 保存到文件 (使用write_file安全写入，避免su -c echo内容过长)
        backup_content = chr(10).join(f'{k}={v}' for k, v in backup.items())
        shell.write_file(f"{SPOOF_BACKUP_DIR}/original.props", backup_content)

    def show_status(self):
        """显示当前伪装状态"""
        title_panel(T("spoof_title"), T("spoof_status"))

        key_props = [
            ("ro.product.model", T("device_model")),
            ("ro.product.manufacturer", T("manufacturer")),
            ("ro.product.brand", T("brand")),
            ("ro.product.name", T("product_name")),
            ("ro.product.device", T("device")),
            ("ro.board.platform", T("platform")),
            ("ro.build.fingerprint", T("spoof_target_fingerprint")),
            ("ro.hardware.egl", T("gpu")),
        ]

        table = Table(border_style="cyan", box=box.ROUNDED, header_style="bold bright_cyan")
        table.add_column(T("spoof_prop_name"), style="cyan", width=24)
        table.add_column(T("spoof_prop_value"), style="white", width=50)

        for prop, label in key_props:
            val = shell.get_prop(prop)
            table.add_row(f"{label}\n[dim]{prop}[/]", val or T("not_available"))

        console.print(table)

    def spoof_model_preset(self):
        """选择预设机型模板 - 一键伪装为知名设备"""
        console.clear()
        title_panel(T("spoof_title"), "选择预设机型模板")

        # 收集所有设备的扁平列表，附带分类信息
        flat_list = []
        for cat_key, category in DEVICE_TEMPLATES.items():
            for idx, dev in enumerate(category["devices"]):
                flat_list.append({
                    "category_key": cat_key,
                    "category_name": category["category_name"],
                    "index_in_category": idx + 1,
                    **dev,
                })

        # 按分类展示设备列表
        current_category = None
        display_index = 0
        for item in flat_list:
            if item["category_name"] != current_category:
                current_category = item["category_name"]
                console.print()
                console.print(f"[bold bright_yellow]═══ {current_category} ═══[/]")
            display_index += 1
            console.print(
                f"  [bold cyan]{display_index:2d}.[/] "
                f"[white]{item['brand']} {item['model_name']}[/] "
                f"[dim]({item['model_code']})[/] "
                f"[yellow]{item['soc']}[/]"
            )

        console.print()
        divider()

        # 用户选择
        total = len(flat_list)
        choices = [str(i) for i in range(1, total + 1)]
        choice = Prompt.ask(
            f"[bold cyan]请输入序号选择设备 (1-{total})[/]",
            choices=choices,
            default="1"
        )
        selected = flat_list[int(choice) - 1]

        # 显示选中设备详情并确认
        console.print()
        console.print(f"[bold green]已选择:[/] {selected['brand']} {selected['model_name']} ({selected['model_code']})")
        console.print(f"[bold green]SoC:[/] {selected['soc']}")

        props_table = Table(border_style="green", box=box.ROUNDED, header_style="bold bright_green")
        props_table.add_column("属性", style="cyan", width=24)
        props_table.add_column("值", style="white", width=55)

        for prop_key, prop_val in selected["props"].items():
            props_table.add_row(prop_key, prop_val)

        console.print(props_table)

        if not Confirm.ask(f"\n[bold yellow]确认应用此设备模板?[/]", default=True):
            return

        loading_spinner("正在应用设备模板...", 1.0)

        # 应用所有属性
        props_to_apply = selected["props"]
        with gradient_progress(len(props_to_apply), "应用设备模板") as (progress, task):
            for prop, value in props_to_apply.items():
                shell.set_prop(prop, value)
                progress.update(task, advance=1)

        popup_message(
            "成功",
            f"已伪装为 {selected['brand']} {selected['model_name']} ({selected['model_code']})",
            "green"
        )
        log_event(
            "SUCCESS", "SPOOF",
            f"预设模板伪装: {selected['brand']} {selected['model_name']} ({selected['model_code']}) [{selected['soc']}]"
        )

    def spoof_model(self, model: str = None, manufacturer: str = None,
                    brand: str = None, device: str = None, name: str = None):
        """伪装机型信息"""
        if not model:
            model = Prompt.ask(f"[cyan]{T('spoof_target_model')}[/]", default="SM-S928B")
        if not manufacturer:
            manufacturer = Prompt.ask(f"[cyan]{T('manufacturer')}[/]", default="samsung")
        if not brand:
            brand = Prompt.ask(f"[cyan]{T('brand')}[/]", default="samsung")
        if not device:
            device = Prompt.ask(f"[cyan]{T('device')}[/]", default="e3q")
        if not name:
            name = Prompt.ask(f"[cyan]{T('product_name')}[/]", default="e3qxx")

        loading_spinner(T("processing"), 1.0)

        props = {
            "ro.product.model": model,
            "ro.product.manufacturer": manufacturer,
            "ro.product.brand": brand,
            "ro.product.name": name,
            "ro.product.device": device,
            "ro.product.board": device,
            "ro.build.product": device,
        }

        with gradient_progress(len(props), T("spoof_model")) as (progress, task):
            for prop, value in props.items():
                shell.set_prop(prop, value)
                progress.update(task, advance=1)

        popup_message(T("success"), T("spoof_apply_ok"), "green")
        log_event("SUCCESS", "SPOOF", T("spoof_model_log").format(manufacturer=manufacturer, model=model))

    def spoof_fingerprint(self, fingerprint: str = None, description: str = None,
                          display_id: str = None):
        """伪装构建指纹"""
        if not fingerprint:
            fingerprint = Prompt.ask(
                f"[cyan]{T('spoof_target_fingerprint')}[/]",
                default="samsung/e3qxx/e3q:14/UP1A.231005.007/S928BXXU1AXK4:user/release-keys"
            )
        if not description:
            description = Prompt.ask(
                f"[cyan]{T('build_description')}[/]",
                default="e3qxx-user 14 UP1A.231005.007 S928BXXU1AXK4 release-keys"
            )
        if not display_id:
            display_id = Prompt.ask(
                f"[cyan]{T('display_id')}[/]",
                default="UP1A.231005.007.S928BXXU1AXK4"
            )

        loading_spinner(T("processing"), 1.0)

        props = {
            "ro.build.fingerprint": fingerprint,
            "ro.build.description": description,
            "ro.build.display.id": display_id,
        }

        with gradient_progress(len(props), T("spoof_fingerprint")) as (progress, task):
            for prop, value in props.items():
                shell.set_prop(prop, value)
                progress.update(task, advance=1)

        popup_message(T("success"), T("spoof_apply_ok"), "green")
        log_event("SUCCESS", "SPOOF", T("spoof_fingerprint_log").format(fp=fingerprint[:50]))

    def spoof_gpu(self, gpu_model: str = None, gpu_vendor: str = None):
        """伪装GPU信息"""
        console.print(f"\n[cyan]{T('spoof_gpu_targets')}[/]")
        gpu_targets = [
            ("Adreno 830", "Qualcomm"),
            ("Adreno 750", "Qualcomm"),
            ("Adreno 740", "Qualcomm"),
            ("Mali-G720", "ARM"),
            ("Immortalis-G720", "ARM"),
            ("Xclipse 940", "Samsung"),
        ]
        for i, (gpu, vendor) in enumerate(gpu_targets, 1):
            console.print(f"  [cyan]{i}.[/] {gpu} ({vendor})")

        choice = Prompt.ask(f"[bold]{T('please_select')}[/]",
                            choices=[str(i) for i in range(1, len(gpu_targets)+1)],
                            default="1")
        gpu_model, gpu_vendor = gpu_targets[int(choice)-1]

        loading_spinner(T("processing"), 1.0)

        props = {
            "ro.hardware.egl": gpu_model.lower().replace(" ", ""),
            "ro.hardware.vulkan": gpu_model.lower().replace(" ", ""),
            "ro.gfx.driver.1": gpu_model,
        }

        for prop, value in props.items():
            shell.set_prop(prop, value)

        popup_message(T("success"), T("spoof_gpu_done").format(gpu=gpu_model), "green")
        log_event("SUCCESS", "SPOOF", T("spoof_gpu_log").format(gpu=gpu_model))

    def spoof_batch_props(self):
        """批量属性伪装"""
        console.print(f"\n[cyan]{T('spoof_custom_props')}[/]")
        console.print(f"[dim]{T('spoof_custom_props_format')}[/]\n")

        props = {}
        while True:
            line = Prompt.ask(f"[dim]{T('prop')}[/]", default="")
            if not line:
                break
            if "=" in line:
                key, val = line.split("=", 1)
                props[key.strip()] = val.strip()

        if not props:
            popup_message(T("warning"), T("no_props_entered"), "yellow")
            return

        loading_spinner(T("processing"), 1.0)

        with gradient_progress(len(props), T("spoof_props")) as (progress, task):
            for prop, value in props.items():
                shell.set_prop(prop, value)
                progress.update(task, advance=1)

        popup_message(T("success"), T("spoof_apply_ok"), "green")
        log_event("SUCCESS", "SPOOF", T("spoof_batch_log").format(count=len(props)))

    def spoof_sensors(self):
        """伪装传感器信息"""
        # 传感器伪装主要通过修改系统属性实现
        sensor_props = {
            "ro.hardware.sensors": "samsung",
            "ro.sensor.proximity": "true",
            "ro.sensor.light": "true",
            "ro.sensor.accelerometer": "true",
            "ro.sensor.gyroscope": "true",
            "ro.sensor.barometer": "true",
            "ro.sensor.magnetometer": "true",
            "ro.sensor.pressure": "true",
            "ro.sensor.humidity": "false",
            "ro.sensor.temperature": "false",
        }

        console.print(f"\n[cyan]{T('spoof_sensor_options')}[/]")
        for prop, val in sensor_props.items():
            current = shell.get_prop(prop)
            console.print(f"  [dim]{prop}[/] = {val} ({T('current_value')}: {current or T('not_available')})")

        if not Confirm.ask(f"\n[bold]{T('confirm_spoof_sensors')}[/]", default=True):
            return

        loading_spinner(T("processing"), 1.0)

        for prop, value in sensor_props.items():
            shell.set_prop(prop, value)

        popup_message(T("success"), T("spoof_apply_ok"), "green")
        log_event("SUCCESS", "SPOOF", T("spoof_sensor_log"))

    def restore_all(self):
        """还原所有伪装"""
        if not Confirm.ask(f"[bold yellow]{T('spoof_restore')}?[/]", default=True):
            return

        loading_spinner(T("processing"), 1.0)

        # 从备份还原
        ok, backup, _ = shell.run(f"cat {SPOOF_BACKUP_DIR}/original.props 2>/dev/null")
        if ok and backup:
            count = 0
            for line in backup.split("\n"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    shell.set_prop(key.strip(), val.strip())
                    count += 1
            popup_message(T("success"), T("spoof_restored_count").format(count=count), "green")
            log_event("SUCCESS", "SPOOF", T("spoof_restore_log"))
        else:
            popup_message(T("warning"), T("no_backup_found"), "yellow")

    def interactive_menu(self):
        """伪装模块交互菜单"""
        while True:
            console.clear()
            title_panel(T("spoof_title"), T("spoof_subtitle"))
            self.show_status()

            console.print()
            console.print(f"  [bold cyan]1.[/] 选择预设机型模板")
            console.print(f"  [bold cyan]2.[/] {T('spoof_model')}")
            console.print(f"  [bold cyan]3.[/] {T('spoof_fingerprint')}")
            console.print(f"  [bold cyan]4.[/] {T('spoof_gpu')}")
            console.print(f"  [bold cyan]5.[/] {T('spoof_props')}")
            console.print(f"  [bold cyan]6.[/] {T('spoof_sensor')}")
            console.print(f"  [bold cyan]7.[/] {T('spoof_restore')}")
            console.print(f"  [bold cyan]0.[/] {T('back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]",
                                choices=["0","1","2","3","4","5","6","7"], default="0")

            if choice == "0":
                break
            elif choice == "1":
                self.spoof_model_preset()
                input(f"\n{T('press_any_key')}")
            elif choice == "2":
                self.spoof_model()
                input(f"\n{T('press_any_key')}")
            elif choice == "3":
                self.spoof_fingerprint()
                input(f"\n{T('press_any_key')}")
            elif choice == "4":
                self.spoof_gpu()
                input(f"\n{T('press_any_key')}")
            elif choice == "5":
                self.spoof_batch_props()
                input(f"\n{T('press_any_key')}")
            elif choice == "6":
                self.spoof_sensors()
                input(f"\n{T('press_any_key')}")
            elif choice == "7":
                self.restore_all()
                input(f"\n{T('press_any_key')}")
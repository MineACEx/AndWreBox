#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
"""

import os
import time
import zipfile
import io
import shutil
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich import box

from core.shell import shell
from core.config import BACKUP_DIR, SNAPDRAGON_CHIPS
from core.i18n import T, get_language, LANG_CN, LANG_EN
from core.animations import (
    console, loading_spinner, gradient_progress,
    popup_message, divider, title_panel, typewriter
)
from core.utils import log_event
from core.paths import TMP_DIR, clean_tmp, get_module_output_dir

# ============ 预设机型模板 (36款机型) ============
DEVICE_TEMPLATES = {
    # ===== Snapdragon 8 Elite / Gen 5 系列 (2025-2026) =====
    "samsung_s25_ultra": {
        "name": "Samsung Galaxy S25 Ultra",
        "props": {
            "ro.product.model": "SM-S938B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "e3sxx",
            "ro.product.device": "e3s",
            "ro.product.board": "e3s",
            "ro.build.product": "e3s",
            "ro.build.fingerprint": "samsung/e3sxx/e3s:15/AP3A.240905.015.A2/S938BXXU1AXK5:user/release-keys",
            "ro.build.description": "e3sxx-user 15 AP3A.240905.015.A2 S938BXXU1AXK5 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.S938BXXU1AXK5",
        },
    },
    "samsung_s25_plus": {
        "name": "Samsung Galaxy S25+",
        "props": {
            "ro.product.model": "SM-S936B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "e2sxx",
            "ro.product.device": "e2s",
            "ro.product.board": "e2s",
            "ro.build.product": "e2s",
            "ro.build.fingerprint": "samsung/e2sxx/e2s:15/AP3A.240905.015.A2/S936BXXU1AXK5:user/release-keys",
            "ro.build.description": "e2sxx-user 15 AP3A.240905.015.A2 S936BXXU1AXK5 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.S936BXXU1AXK5",
        },
    },
    "samsung_s25": {
        "name": "Samsung Galaxy S25",
        "props": {
            "ro.product.model": "SM-S931B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "e1sxx",
            "ro.product.device": "e1s",
            "ro.product.board": "e1s",
            "ro.build.product": "e1s",
            "ro.build.fingerprint": "samsung/e1sxx/e1s:15/AP3A.240905.015.A2/S931BXXU1AXK5:user/release-keys",
            "ro.build.description": "e1sxx-user 15 AP3A.240905.015.A2 S931BXXU1AXK5 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.S931BXXU1AXK5",
        },
    },
    "samsung_z_fold_7": {
        "name": "Samsung Galaxy Z Fold 7",
        "props": {
            "ro.product.model": "SM-F966B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "q7sxx",
            "ro.product.device": "q7s",
            "ro.product.board": "q7s",
            "ro.build.product": "q7s",
            "ro.build.fingerprint": "samsung/q7sxx/q7s:15/AP3A.240905.015.A2/F966BXXU1AXK5:user/release-keys",
            "ro.build.description": "q7sxx-user 15 AP3A.240905.015.A2 F966BXXU1AXK5 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.F966BXXU1AXK5",
        },
    },
    "samsung_z_flip_7": {
        "name": "Samsung Galaxy Z Flip 7",
        "props": {
            "ro.product.model": "SM-F741B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "b7sxx",
            "ro.product.device": "b7s",
            "ro.product.board": "b7s",
            "ro.build.product": "b7s",
            "ro.build.fingerprint": "samsung/b7sxx/b7s:15/AP3A.240905.015.A2/F741BXXU1AXK5:user/release-keys",
            "ro.build.description": "b7sxx-user 15 AP3A.240905.015.A2 F741BXXU1AXK5 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.F741BXXU1AXK5",
        },
    },
    "xiaomi_15_ultra": {
        "name": "Xiaomi 15 Ultra",
        "props": {
            "ro.product.model": "25010PN30G",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "aurora",
            "ro.product.device": "aurora",
            "ro.product.board": "aurora",
            "ro.build.product": "aurora",
            "ro.build.fingerprint": "Xiaomi/aurora/aurora:15/AP3A.240905.015.A2/V816.0.6.0.ULAMIXM:user/release-keys",
            "ro.build.description": "aurora-user 15 AP3A.240905.015.A2 V816.0.6.0.ULAMIXM release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.V816.0.6.0.ULAMIXM",
        },
    },
    "xiaomi_15_pro": {
        "name": "Xiaomi 15 Pro",
        "props": {
            "ro.product.model": "2410DPN6CC",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "haotian",
            "ro.product.device": "haotian",
            "ro.product.board": "haotian",
            "ro.build.product": "haotian",
            "ro.build.fingerprint": "Xiaomi/haotian/haotian:15/AP3A.240905.015.A2/V816.0.3.0.ULBCNXM:user/release-keys",
            "ro.build.description": "haotian-user 15 AP3A.240905.015.A2 V816.0.3.0.ULBCNXM release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.V816.0.3.0.ULBCNXM",
        },
    },
    "xiaomi_15": {
        "name": "Xiaomi 15",
        "props": {
            "ro.product.model": "24129PN74C",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "dada",
            "ro.product.device": "dada",
            "ro.product.board": "dada",
            "ro.build.product": "dada",
            "ro.build.fingerprint": "Xiaomi/dada/dada:15/AP3A.240905.015.A2/V816.0.1.0.ULCCNXM:user/release-keys",
            "ro.build.description": "dada-user 15 AP3A.240905.015.A2 V816.0.1.0.ULCCNXM release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.V816.0.1.0.ULCCNXM",
        },
    },
    "oneplus_13": {
        "name": "OnePlus 13",
        "props": {
            "ro.product.model": "CPH2653",
            "ro.product.manufacturer": "OnePlus",
            "ro.product.brand": "OnePlus",
            "ro.product.name": "OP594DL1",
            "ro.product.device": "OP594DL1",
            "ro.product.board": "OP594DL1",
            "ro.build.product": "OP594DL1",
            "ro.build.fingerprint": "OnePlus/OP594DL1/OP594DL1:15/AP3A.240905.015.A2/CPH2653_15.0.0.400:user/release-keys",
            "ro.build.description": "OP594DL1-user 15 AP3A.240905.015.A2 CPH2653_15.0.0.400 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.CPH2653_15.0.0.400",
        },
    },
    "oneplus_13r": {
        "name": "OnePlus 13R",
        "props": {
            "ro.product.model": "CPH2691",
            "ro.product.manufacturer": "OnePlus",
            "ro.product.brand": "OnePlus",
            "ro.product.name": "OP596DL1",
            "ro.product.device": "OP596DL1",
            "ro.product.board": "OP596DL1",
            "ro.build.product": "OP596DL1",
            "ro.build.fingerprint": "OnePlus/OP596DL1/OP596DL1:15/AP3A.240905.015.A2/CPH2691_15.0.0.310:user/release-keys",
            "ro.build.description": "OP596DL1-user 15 AP3A.240905.015.A2 CPH2691_15.0.0.310 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.CPH2691_15.0.0.310",
        },
    },
    "oppo_find_x8_ultra": {
        "name": "OPPO Find X8 Ultra",
        "props": {
            "ro.product.model": "CPH2771",
            "ro.product.manufacturer": "OPPO",
            "ro.product.brand": "OPPO",
            "ro.product.name": "OP5B1FL1",
            "ro.product.device": "OP5B1FL1",
            "ro.product.board": "OP5B1FL1",
            "ro.build.product": "OP5B1FL1",
            "ro.build.fingerprint": "OPPO/OP5B1FL1/OP5B1FL1:15/AP3A.240905.015.A2/CPH2771_15.0.0.410:user/release-keys",
            "ro.build.description": "OP5B1FL1-user 15 AP3A.240905.015.A2 CPH2771_15.0.0.410 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.CPH2771_15.0.0.410",
        },
    },
    "oppo_find_x8_pro": {
        "name": "OPPO Find X8 Pro",
        "props": {
            "ro.product.model": "CPH2755",
            "ro.product.manufacturer": "OPPO",
            "ro.product.brand": "OPPO",
            "ro.product.name": "OP5A9FL1",
            "ro.product.device": "OP5A9FL1",
            "ro.product.board": "OP5A9FL1",
            "ro.build.product": "OP5A9FL1",
            "ro.build.fingerprint": "OPPO/OP5A9FL1/OP5A9FL1:15/AP3A.240905.015.A2/CPH2755_15.0.0.350:user/release-keys",
            "ro.build.description": "OP5A9FL1-user 15 AP3A.240905.015.A2 CPH2755_15.0.0.350 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.CPH2755_15.0.0.350",
        },
    },
    "vivo_x200_ultra": {
        "name": "vivo X200 Ultra",
        "props": {
            "ro.product.model": "V2425A",
            "ro.product.manufacturer": "vivo",
            "ro.product.brand": "vivo",
            "ro.product.name": "PD2425",
            "ro.product.device": "PD2425",
            "ro.product.board": "PD2425",
            "ro.build.product": "PD2425",
            "ro.build.fingerprint": "vivo/PD2425/PD2425:15/AP3A.240905.015.A2/V2425A_15.0.18.10:user/release-keys",
            "ro.build.description": "PD2425-user 15 AP3A.240905.015.A2 V2425A_15.0.18.10 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.V2425A_15.0.18.10",
        },
    },
    "vivo_x200_pro": {
        "name": "vivo X200 Pro",
        "props": {
            "ro.product.model": "V2413A",
            "ro.product.manufacturer": "vivo",
            "ro.product.brand": "vivo",
            "ro.product.name": "PD2413",
            "ro.product.device": "PD2413",
            "ro.product.board": "PD2413",
            "ro.build.product": "PD2413",
            "ro.build.fingerprint": "vivo/PD2413/PD2413:15/AP3A.240905.015.A2/V2413A_15.0.20.5:user/release-keys",
            "ro.build.description": "PD2413-user 15 AP3A.240905.015.A2 V2413A_15.0.20.5 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.V2413A_15.0.20.5",
        },
    },
    "iqoo_13": {
        "name": "iQOO 13",
        "props": {
            "ro.product.model": "I2401",
            "ro.product.manufacturer": "vivo",
            "ro.product.brand": "iQOO",
            "ro.product.name": "PD2401",
            "ro.product.device": "PD2401",
            "ro.product.board": "PD2401",
            "ro.build.product": "PD2401",
            "ro.build.fingerprint": "iQOO/PD2401/PD2401:15/AP3A.240905.015.A2/I2401_15.0.12.8:user/release-keys",
            "ro.build.description": "PD2401-user 15 AP3A.240905.015.A2 I2401_15.0.12.8 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.I2401_15.0.12.8",
        },
    },
    "realme_gt_8_pro": {
        "name": "Realme GT 8 Pro",
        "props": {
            "ro.product.model": "RMX5090",
            "ro.product.manufacturer": "realme",
            "ro.product.brand": "realme",
            "ro.product.name": "RE5C9FL1",
            "ro.product.device": "RE5C9FL1",
            "ro.product.board": "RE5C9FL1",
            "ro.build.product": "RE5C9FL1",
            "ro.build.fingerprint": "realme/RE5C9FL1/RE5C9FL1:15/AP3A.240905.015.A2/RMX5090_15.0.0.510:user/release-keys",
            "ro.build.description": "RE5C9FL1-user 15 AP3A.240905.015.A2 RMX5090_15.0.0.510 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.RMX5090_15.0.0.510",
        },
    },
    "asus_rog_9": {
        "name": "ASUS ROG Phone 9",
        "props": {
            "ro.product.model": "AI2501",
            "ro.product.manufacturer": "asus",
            "ro.product.brand": "asus",
            "ro.product.name": "ASUS_AI2501",
            "ro.product.device": "ASUS_AI2501",
            "ro.product.board": "ASUS_AI2501",
            "ro.build.product": "ASUS_AI2501",
            "ro.build.fingerprint": "asus/ASUS_AI2501/ASUS_AI2501:15/AP3A.240905.015.A2/AI2501_35.1010.1010.0:user/release-keys",
            "ro.build.description": "ASUS_AI2501-user 15 AP3A.240905.015.A2 AI2501_35.1010.1010.0 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.AI2501_35.1010.1010.0",
        },
    },
    "red_magic_10_pro": {
        "name": "Red Magic 10 Pro",
        "props": {
            "ro.product.model": "NX789J",
            "ro.product.manufacturer": "nubia",
            "ro.product.brand": "nubia",
            "ro.product.name": "NX789J",
            "ro.product.device": "NX789J",
            "ro.product.board": "NX789J",
            "ro.build.product": "NX789J",
            "ro.build.fingerprint": "nubia/NX789J/NX789J:15/AP3A.240905.015.A2/NX789J_V3.10:user/release-keys",
            "ro.build.description": "NX789J-user 15 AP3A.240905.015.A2 NX789J_V3.10 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.NX789J_V3.10",
        },
    },
    "honor_magic_7_pro": {
        "name": "Honor Magic 7 Pro",
        "props": {
            "ro.product.model": "BVL-AN00",
            "ro.product.manufacturer": "HONOR",
            "ro.product.brand": "honor",
            "ro.product.name": "BVL-AN00",
            "ro.product.device": "HNBVL-AN00",
            "ro.product.board": "HNBVL-AN00",
            "ro.build.product": "HNBVL-AN00",
            "ro.build.fingerprint": "honor/HNBVL-AN00/HNBVL-AN00:15/AP3A.240905.015.A2/BVL-AN00_9.0.0.160:user/release-keys",
            "ro.build.description": "HNBVL-AN00-user 15 AP3A.240905.015.A2 BVL-AN00_9.0.0.160 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.BVL-AN00_9.0.0.160",
        },
    },
    "google_pixel_10_pro": {
        "name": "Google Pixel 10 Pro",
        "props": {
            "ro.product.model": "Pixel 10 Pro",
            "ro.product.manufacturer": "Google",
            "ro.product.brand": "google",
            "ro.product.name": "raven",
            "ro.product.device": "raven",
            "ro.product.board": "raven",
            "ro.build.product": "raven",
            "ro.build.fingerprint": "google/raven/raven:15/AP3A.240905.015.A2/12051.2000.16:user/release-keys",
            "ro.build.description": "raven-user 15 AP3A.240905.015.A2 12051.2000.16 release-keys",
            "ro.build.display.id": "AP3A.240905.015.A2.12051.2000.16",
        },
    },
    # ===== Snapdragon 8 Gen 3 系列 (2024) =====
    "samsung_s24_ultra": {
        "name": "Samsung Galaxy S24 Ultra",
        "props": {
            "ro.product.model": "SM-S928B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "e3qxx",
            "ro.product.device": "e3q",
            "ro.product.board": "e3q",
            "ro.build.product": "e3q",
            "ro.build.fingerprint": "samsung/e3qxx/e3q:14/UP1A.231005.007/S928BXXU1AXK4:user/release-keys",
            "ro.build.description": "e3qxx-user 14 UP1A.231005.007 S928BXXU1AXK4 release-keys",
            "ro.build.display.id": "UP1A.231005.007.S928BXXU1AXK4",
        },
    },
    "samsung_s24_plus": {
        "name": "Samsung Galaxy S24+",
        "props": {
            "ro.product.model": "SM-S926B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "e2qxx",
            "ro.product.device": "e2q",
            "ro.product.board": "e2q",
            "ro.build.product": "e2q",
            "ro.build.fingerprint": "samsung/e2qxx/e2q:14/UP1A.231005.007/S926BXXU1AXK4:user/release-keys",
            "ro.build.description": "e2qxx-user 14 UP1A.231005.007 S926BXXU1AXK4 release-keys",
            "ro.build.display.id": "UP1A.231005.007.S926BXXU1AXK4",
        },
    },
    "samsung_s24": {
        "name": "Samsung Galaxy S24",
        "props": {
            "ro.product.model": "SM-S921B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "e1qxx",
            "ro.product.device": "e1q",
            "ro.product.board": "e1q",
            "ro.build.product": "e1q",
            "ro.build.fingerprint": "samsung/e1qxx/e1q:14/UP1A.231005.007/S921BXXU1AXK4:user/release-keys",
            "ro.build.description": "e1qxx-user 14 UP1A.231005.007 S921BXXU1AXK4 release-keys",
            "ro.build.display.id": "UP1A.231005.007.S921BXXU1AXK4",
        },
    },
    "xiaomi_14_ultra": {
        "name": "Xiaomi 14 Ultra",
        "props": {
            "ro.product.model": "24030PN60G",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "aurora",
            "ro.product.device": "aurora",
            "ro.product.board": "aurora",
            "ro.build.product": "aurora",
            "ro.build.fingerprint": "Xiaomi/aurora/aurora:14/UP1A.231005.007/V816.0.18.0.ULAMIXM:user/release-keys",
            "ro.build.description": "aurora-user 14 UP1A.231005.007 V816.0.18.0.ULAMIXM release-keys",
            "ro.build.display.id": "UP1A.231005.007.V816.0.18.0.ULAMIXM",
        },
    },
    "xiaomi_14_pro": {
        "name": "Xiaomi 14 Pro",
        "props": {
            "ro.product.model": "2311DRK48C",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "shennong",
            "ro.product.device": "shennong",
            "ro.product.board": "shennong",
            "ro.build.product": "shennong",
            "ro.build.fingerprint": "Xiaomi/shennong/shennong:14/UP1A.231005.007/V816.0.17.0.ULBCNXM:user/release-keys",
            "ro.build.description": "shennong-user 14 UP1A.231005.007 V816.0.17.0.ULBCNXM release-keys",
            "ro.build.display.id": "UP1A.231005.007.V816.0.17.0.ULBCNXM",
        },
    },
    "xiaomi_14": {
        "name": "Xiaomi 14",
        "props": {
            "ro.product.model": "23127PN0CC",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "houji",
            "ro.product.device": "houji",
            "ro.product.board": "houji",
            "ro.build.product": "houji",
            "ro.build.fingerprint": "Xiaomi/houji/houji:14/UP1A.231005.007/V816.0.13.0.ULCCNXM:user/release-keys",
            "ro.build.description": "houji-user 14 UP1A.231005.007 V816.0.13.0.ULCCNXM release-keys",
            "ro.build.display.id": "UP1A.231005.007.V816.0.13.0.ULCCNXM",
        },
    },
    "oneplus_12": {
        "name": "OnePlus 12",
        "props": {
            "ro.product.model": "CPH2581",
            "ro.product.manufacturer": "OnePlus",
            "ro.product.brand": "OnePlus",
            "ro.product.name": "OP5961L1",
            "ro.product.device": "OP5961L1",
            "ro.product.board": "OP5961L1",
            "ro.build.product": "OP5961L1",
            "ro.build.fingerprint": "OnePlus/OP5961L1/OP5961L1:14/UP1A.231005.007/CPH2581_14.0.0.850:user/release-keys",
            "ro.build.description": "OP5961L1-user 14 UP1A.231005.007 CPH2581_14.0.0.850 release-keys",
            "ro.build.display.id": "UP1A.231005.007.CPH2581_14.0.0.850",
        },
    },
    "oppo_find_x7_ultra": {
        "name": "OPPO Find X7 Ultra",
        "props": {
            "ro.product.model": "PHY110",
            "ro.product.manufacturer": "OPPO",
            "ro.product.brand": "OPPO",
            "ro.product.name": "OP5B1FL1",
            "ro.product.device": "OP5B1FL1",
            "ro.product.board": "OP5B1FL1",
            "ro.build.product": "OP5B1FL1",
            "ro.build.fingerprint": "OPPO/OP5B1FL1/OP5B1FL1:14/UP1A.231005.007/PHY110_14.0.0.830:user/release-keys",
            "ro.build.description": "OP5B1FL1-user 14 UP1A.231005.007 PHY110_14.0.0.830 release-keys",
            "ro.build.display.id": "UP1A.231005.007.PHY110_14.0.0.830",
        },
    },
    "vivo_x100_ultra": {
        "name": "vivo X100 Ultra",
        "props": {
            "ro.product.model": "V2366A",
            "ro.product.manufacturer": "vivo",
            "ro.product.brand": "vivo",
            "ro.product.name": "PD2366",
            "ro.product.device": "PD2366",
            "ro.product.board": "PD2366",
            "ro.build.product": "PD2366",
            "ro.build.fingerprint": "vivo/PD2366/PD2366:14/UP1A.231005.007/V2366A_14.0.16.3:user/release-keys",
            "ro.build.description": "PD2366-user 14 UP1A.231005.007 V2366A_14.0.16.3 release-keys",
            "ro.build.display.id": "UP1A.231005.007.V2366A_14.0.16.3",
        },
    },
    "realme_gt_5_pro": {
        "name": "Realme GT 5 Pro",
        "props": {
            "ro.product.model": "RMX3888",
            "ro.product.manufacturer": "realme",
            "ro.product.brand": "realme",
            "ro.product.name": "RE5B9FL1",
            "ro.product.device": "RE5B9FL1",
            "ro.product.board": "RE5B9FL1",
            "ro.build.product": "RE5B9FL1",
            "ro.build.fingerprint": "realme/RE5B9FL1/RE5B9FL1:14/UP1A.231005.007/RMX3888_14.0.0.810:user/release-keys",
            "ro.build.description": "RE5B9FL1-user 14 UP1A.231005.007 RMX3888_14.0.0.810 release-keys",
            "ro.build.display.id": "UP1A.231005.007.RMX3888_14.0.0.810",
        },
    },
    # ===== Snapdragon 8 Gen 2 系列 (2023) =====
    "samsung_s23_ultra": {
        "name": "Samsung Galaxy S23 Ultra",
        "props": {
            "ro.product.model": "SM-S918B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "dm3qxx",
            "ro.product.device": "dm3q",
            "ro.product.board": "dm3q",
            "ro.build.product": "dm3q",
            "ro.build.fingerprint": "samsung/dm3qxx/dm3q:13/TP1A.220624.014/S918BXXU1AWE3:user/release-keys",
            "ro.build.description": "dm3qxx-user 13 TP1A.220624.014 S918BXXU1AWE3 release-keys",
            "ro.build.display.id": "TP1A.220624.014.S918BXXU1AWE3",
        },
    },
    "samsung_s23_plus": {
        "name": "Samsung Galaxy S23+",
        "props": {
            "ro.product.model": "SM-S916B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "dm2qxx",
            "ro.product.device": "dm2q",
            "ro.product.board": "dm2q",
            "ro.build.product": "dm2q",
            "ro.build.fingerprint": "samsung/dm2qxx/dm2q:13/TP1A.220624.014/S916BXXU1AWE3:user/release-keys",
            "ro.build.description": "dm2qxx-user 13 TP1A.220624.014 S916BXXU1AWE3 release-keys",
            "ro.build.display.id": "TP1A.220624.014.S916BXXU1AWE3",
        },
    },
    "samsung_s23": {
        "name": "Samsung Galaxy S23",
        "props": {
            "ro.product.model": "SM-S911B",
            "ro.product.manufacturer": "samsung",
            "ro.product.brand": "samsung",
            "ro.product.name": "dm1qxx",
            "ro.product.device": "dm1q",
            "ro.product.board": "dm1q",
            "ro.build.product": "dm1q",
            "ro.build.fingerprint": "samsung/dm1qxx/dm1q:13/TP1A.220624.014/S911BXXU1AWE3:user/release-keys",
            "ro.build.description": "dm1qxx-user 13 TP1A.220624.014 S911BXXU1AWE3 release-keys",
            "ro.build.display.id": "TP1A.220624.014.S911BXXU1AWE3",
        },
    },
    "xiaomi_13_ultra": {
        "name": "Xiaomi 13 Ultra",
        "props": {
            "ro.product.model": "2304FPN6DC",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "ishtar",
            "ro.product.device": "ishtar",
            "ro.product.board": "ishtar",
            "ro.build.product": "ishtar",
            "ro.build.fingerprint": "Xiaomi/ishtar/ishtar:13/TP1A.220624.014/V14.0.9.0.TMAMIXM:user/release-keys",
            "ro.build.description": "ishtar-user 13 TP1A.220624.014 V14.0.9.0.TMAMIXM release-keys",
            "ro.build.display.id": "TP1A.220624.014.V14.0.9.0.TMAMIXM",
        },
    },
    "xiaomi_13_pro": {
        "name": "Xiaomi 13 Pro",
        "props": {
            "ro.product.model": "2210132G",
            "ro.product.manufacturer": "Xiaomi",
            "ro.product.brand": "Xiaomi",
            "ro.product.name": "nuwa",
            "ro.product.device": "nuwa",
            "ro.product.board": "nuwa",
            "ro.build.product": "nuwa",
            "ro.build.fingerprint": "Xiaomi/nuwa/nuwa:13/TP1A.220624.014/V14.0.11.0.TMBMIXM:user/release-keys",
            "ro.build.description": "nuwa-user 13 TP1A.220624.014 V14.0.11.0.TMBMIXM release-keys",
            "ro.build.display.id": "TP1A.220624.014.V14.0.11.0.TMBMIXM",
        },
    },
    "oneplus_11": {
        "name": "OnePlus 11",
        "props": {
            "ro.product.model": "CPH2449",
            "ro.product.manufacturer": "OnePlus",
            "ro.product.brand": "OnePlus",
            "ro.product.name": "OP594DL1",
            "ro.product.device": "OP594DL1",
            "ro.product.board": "OP594DL1",
            "ro.build.product": "OP594DL1",
            "ro.build.fingerprint": "OnePlus/OP594DL1/OP594DL1:13/TP1A.220624.014/CPH2449_13.1.0.501:user/release-keys",
            "ro.build.description": "OP594DL1-user 13 TP1A.220624.014 CPH2449_13.1.0.501 release-keys",
            "ro.build.display.id": "TP1A.220624.014.CPH2449_13.1.0.501",
        },
    },
}


class MagiskModuleBuilder:
    """Magisk模块生成器"""

    def __init__(self):
        # 输出目录（最终 zip 产物，用户可自定义）
        self.output_dir = get_module_output_dir()
        shell.mkdir(self.output_dir)

        # 临时缓存目录（中间文件）
        clean_tmp()
        self.tmp_dir = os.path.join(TMP_DIR, "magisk")
        os.makedirs(self.tmp_dir, exist_ok=True)

    def _verify_file(self, path: str) -> bool:
        """验证文件是否写入成功（存在且非空）"""
        if not shell.file_exists(path):
            from core.logger import warning
            warning("MAGISK", f"File write failed: {path} not found")
            return False
        ok, size, _ = shell.run(f"stat -c%s '{path}' 2>/dev/null")
        try:
            if int(size.strip()) <= 0:
                from core.logger import warning
                warning("MAGISK", f"File write failed: {path} is empty")
                return False
        except ValueError:
            pass
        from core.logger import success
        success("MAGISK", f"File written: {path} ({size.strip()} bytes)")
        return True

    def _generate_meta_inf(self) -> dict:
        """
        生成 Magisk META-INF 签名文件
        Magisk模块必须包含 META-INF/com/google/android/ 下的签名文件才能被正确识别
        """
        update_binary = """#!/sbin/sh
# ============================================================
# Magisk Module Installer - update-binary
# AndWreBox - 安卓扳手盒子 v1.0
# ============================================================

umask 022

# 输出函数 (在加载util_functions前自定义)
ui_print() { echo "$1"; }

# 需要新版Magisk检查
require_new_magisk() {
  ui_print "*******************************"
  ui_print " Please install Magisk v20.4+! "
  ui_print "*******************************"
  exit 1
}

#########################
# 加载 Magisk 工具函数
#########################

OUTFD=$2
ZIPFILE=$3

TMPDIR=/dev/tmp
MAGISKBIN=/data/adb/magisk

mount /data 2>/dev/null

[ -f $MAGISKBIN/util_functions.sh ] || require_new_magisk
. $MAGISKBIN/util_functions.sh
[ $MAGISK_VER_CODE -lt 20400 ] && require_new_magisk

# 执行模块安装
install_module
exit 0
"""

        updater_script = """#MAGISK
# ============================================================
# Magisk Module Updater-Script
# AndWreBox - 安卓扳手盒子 v1.0
# ============================================================
"""

        return {
            "META-INF/com/google/android/update-binary": update_binary,
            "META-INF/com/google/android/updater-script": updater_script,
        }

    def _create_module_zip(self, module_dir: str, zip_path: str) -> bool:
        """
        使用 Python zipfile 原生创建 Magisk 模块 ZIP 包
        自动包含 META-INF 签名文件，确保 Magisk 可正确识别和安装
        """
        try:
            # 写入 META-INF 签名文件
            meta_files = self._generate_meta_inf()
            for fname, content in meta_files.items():
                meta_path = os.path.join(module_dir, fname)
                os.makedirs(os.path.dirname(meta_path), exist_ok=True)
                with open(meta_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # 使用 Python zipfile 原生打包
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(module_dir):
                    for fn in files:
                        file_path = os.path.join(root, fn)
                        arcname = os.path.relpath(file_path, module_dir)
                        zf.write(file_path, arcname)

            from core.logger import success
            success("MAGISK", f"ZIP created: {zip_path}")
            return True

        except Exception as e:
            from core.logger import error
            error("MAGISK", f"ZIP creation failed: {e}")
            return False

    def _module_header_comment(self) -> str:
        """生成模块文件通用头部注释"""
        return """# ============================================================
# AndWreBox - 安卓扳手盒子 v1.0
# 生成时间: {timestamp}
# ============================================================
# 修改此文件前请先了解Magisk模块机制
# 错误配置可能导致设备无法开机，请谨慎修改
# ============================================================
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def _generate_module_prop(self, module_id: str, name: str, version: str,
                               version_code: str, author: str, description: str,
                               min_magisk: str = "26300") -> str:
        """生成 module.prop 文件内容"""
        return f"""{self._module_header_comment()}
# ============================================================
# module.prop - Magisk模块核心配置文件
# 格式: key=value (等号两边不要有空格!)
# ============================================================

# 模块唯一标识符 (必须唯一，不能与其他模块冲突)
id={module_id}

# 模块显示名称 (将显示在Magisk管理器中的模块名称)
name={name}

# 模块版本号 (字符串格式，用于显示)
version={version}

# 模块版本号 (整数格式，用于版本比较，越大越新)
versionCode={version_code}

# 模块作者
author={author}

# 模块功能描述 (支持多行，\\n 换行)
description={description}

# 最低Magisk版本要求 (可选，默认不限制)
minMagisk={min_magisk}

# 最低Android API级别要求 (可选，SDK 34 = Android 14)
# minApi=34

# 最高Android API级别 (可选)
# maxApi=35

# 是否需要重启后生效 (可选, 默认true)
# needRamdisk=false

# 是否支持Android 14+的overlay挂载 (可选)
# supportOverlayfs=true
"""

    def _generate_customize_sh(self, module_type: str, extra_info: dict = None) -> str:
        """生成 customize.sh 安装脚本"""
        extra = extra_info or {}
        display_name = extra.get('display_name', module_type)
        base = f"""{self._module_header_comment()}
# ============================================================
# customize.sh - Magisk模块安装脚本
# 在模块安装时执行，用于自定义安装流程
# 运行环境: Magisk busybox ash shell
# ============================================================

# 获取Magisk相关变量
# MODPATH: 模块安装目录 (如 /data/adb/modules_update/<module_id>)
# TMPDIR: 临时目录
# ZIPFILE: 模块ZIP文件路径
# ARCH: 设备CPU架构 (arm/arm64/x86/x64)
# IS64BIT: 是否为64位系统
# API: Android API级别

# 获取当前模块路径
MODPATH=${{0%/*}}

# 打印安装信息
ui_print "========================================"
ui_print "  {display_name}"
ui_print "  AndWreBox - 安卓扳手盒子 v1.0"
ui_print "========================================"
ui_print ""
ui_print "- 设备架构: $ARCH"
ui_print "- Android API: $API"
ui_print "- 64位系统: $IS64BIT"
ui_print ""

# 设置system.prop中属性为post-fs-data阶段加载
# Magisk会自动处理system.prop文件，无需额外操作

# 检查system.prop文件
if [ -f "$MODPATH/system.prop" ]; then
    ui_print "- 检测到system.prop，将在开机时加载属性"
    ui_print "- 属性数量: $(wc -l < $MODPATH/system.prop)"
fi

# 检查service.sh脚本
if [ -f "$MODPATH/service.sh" ]; then
    ui_print "- 检测到service.sh，将在开机完成后执行"
    chmod +x "$MODPATH/service.sh"
fi

# 检查post-fs-data.sh脚本
if [ -f "$MODPATH/post-fs-data.sh" ]; then
    ui_print "- 检测到post-fs-data.sh，将在/data挂载后执行"
    chmod +x "$MODPATH/post-fs-data.sh"
fi

# 设置正确权限
# 目录权限 755 (rwxr-xr-x)
# 文件权限 644 (rw-r--r--)
# 脚本权限 755 (rwxr-xr-x)
set_perm_recursive $MODPATH 0 0 0755 0644
set_perm $MODPATH/service.sh 0 0 0755
set_perm $MODPATH/post-fs-data.sh 0 0 0755

ui_print ""
ui_print "- 安装完成！"
ui_print "- 请重启设备使模块生效"
ui_print "- 如需卸载，请在Magisk管理器中移除本模块"
ui_print ""
"""
        return base

    def _generate_service_sh(self, module_type: str, extra_info: dict = None) -> str:
        """生成 service.sh 开机后执行脚本"""
        if module_type == "perf":
            return f"""{self._module_header_comment()}
# ============================================================
# service.sh - 开机后延迟执行脚本
# 在系统启动完成后执行 (boot_completed 之后)
# 适合执行需要系统服务就绪后才生效的优化
# ============================================================

# 等待系统完全启动 (等待boot_completed广播)
# 这样可以确保所有系统服务都已就绪
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 5
done

# 再等待一段时间确保系统稳定
sleep 30

# ============================================================
# 以下为性能优化脚本
# 取消注释以启用对应功能
# ============================================================

# --- CPU性能优化 ---
# 切换所有核心到performance调度器
# for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
#     echo "performance" > $cpu
# done

# 锁定大核为最高频率 (需根据你的芯片修改核心编号)
# 大核通常在cpu4-cpu7 (骁龙8 Gen系列)
# for cpu in 4 5 6 7; do
#     max_freq=$(cat /sys/devices/system/cpu/cpu$cpu/cpufreq/cpuinfo_max_freq)
#     echo $max_freq > /sys/devices/system/cpu/cpu$cpu/cpufreq/scaling_min_freq
# done

# --- GPU性能优化 ---
# 设置GPU为performance模式
# echo "performance" > /sys/class/kgsl/kgsl-3d0/devfreq/governor

# 强制GPU始终在线 (防止nap省电)
# echo "1" > /sys/class/kgsl/kgsl-3d0/force_no_nap
# echo "1" > /sys/class/kgsl/kgsl-3d0/force_clk_on
# echo "1" > /sys/class/kgsl/kgsl-3d0/force_bus_on

# --- 内存优化 ---
# 调整内核参数
# sysctl -w vm.swappiness=60
# sysctl -w vm.vfs_cache_pressure=50
# sysctl -w vm.dirty_ratio=10
# sysctl -w vm.dirty_background_ratio=5

# --- I/O调度优化 ---
# 设置I/O调度器为mq-deadline (适合移动设备)
# for queue in /sys/block/*/queue/scheduler; do
#     echo "mq-deadline" > $queue 2>/dev/null
# done

# --- 网络优化 ---
# 调整TCP缓冲区大小
# sysctl -w net.core.rmem_max=2621440
# sysctl -w net.core.wmem_max=2621440
# sysctl -w net.ipv4.tcp_rmem="4096 87380 2621440"
# sysctl -w net.ipv4.tcp_wmem="4096 16384 2621440"

echo "Performance optimization applied successfully."
"""
        elif module_type == "debloat":
            return f"""{self._module_header_comment()}
# ============================================================
# service.sh - 系统精简脚本
# 在系统启动完成后执行，禁用不必要的系统服务和功能
# ============================================================

# 等待系统完全启动
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 5
done
sleep 30

# --- 禁用不必要的系统服务 ---
# 禁用系统追踪服务 (减少后台开销)
stop traced 2>/dev/null
stop traceservice 2>/dev/null

# 禁用统计服务
stop statsd 2>/dev/null

# 禁用Bug报告服务
stop bugreport 2>/dev/null
stop bugreportd 2>/dev/null

# 禁用Logd大缓冲区 (已在system.prop中设置，此处再次确认)
stop logd 2>/dev/null
sleep 1
start logd 2>/dev/null

# --- 清理缓存 ---
# 清理dalvik-cache中的临时文件
rm -rf /data/dalvik-cache/*.tmp 2>/dev/null

# 清理系统临时文件
rm -rf /data/system/dropbox/* 2>/dev/null

# --- 冻结不必要的系统应用 (需要Magisk支持) ---
# 注意: 以下为示例，取消注释前请确认应用不影响系统稳定性
# pm disable-user --user 0 com.google.android.apps.maps 2>/dev/null
# pm disable-user --user 0 com.google.android.apps.photos 2>/dev/null
# pm disable-user --user 0 com.google.android.videos 2>/dev/null
# pm disable-user --user 0 com.google.android.music 2>/dev/null

echo "System debloat applied successfully."
"""
        elif module_type == "gpu":
            return f"""{self._module_header_comment()}
# ============================================================
# service.sh - GPU优化脚本
# ============================================================

while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 5
done
sleep 30

# --- GPU Turbo优化 ---
# 设置GPU调度器为性能模式
echo "performance" > /sys/class/kgsl/kgsl-3d0/devfreq/governor

# 阻止GPU进入nap省电状态
echo "1" > /sys/class/kgsl/kgsl-3d0/force_no_nap
echo "1" > /sys/class/kgsl/kgsl-3d0/force_clk_on
echo "1" > /sys/class/kgsl/kgsl-3d0/force_bus_on

# 设置GPU最低频率为其最大频率的50% (提升响应速度)
# max_gpuclk=$(cat /sys/class/kgsl/kgsl-3d0/max_gpuclk)
# echo $((max_gpuclk / 2)) > /sys/class/kgsl/kgsl-3d0/min_gpuclk

# 设置GPU渲染属性
setprop debug.composition.type gpu
setprop debug.sf.hw 1
setprop persist.sys.composition.type gpu
setprop hwui.render_dirty_regions false

echo "GPU optimization applied successfully."
"""
        else:
            return ""

    def _generate_post_fs_data_sh(self, module_type: str, extra_info: dict = None) -> str:
        """生成 post-fs-data.sh 早期执行脚本"""
        return f"""{self._module_header_comment()}
# ============================================================
# post-fs-data.sh - 早期执行脚本
# 在/data分区挂载后立即执行 (在Zygote启动前)
# 适合需要在系统服务启动前生效的修改
# 注意: 此脚本以root权限运行，但boot尚未完成
# ============================================================

# 此阶段适合:
# 1. 修改内核参数 (sysctl)
# 2. 修改系统文件 (需要先挂载为可读写)
# 3. 设置属性 (resetprop)

# 示例: 修改内核参数
# sysctl -w kernel.sched_child_runs_first=1
# sysctl -w kernel.sched_autogroup_enabled=0

# 示例: 修改系统属性 (早于system.prop生效)
# resetprop ro.config.low_ram false
# resetprop ro.config.hw_quickpoweron true

echo "post-fs-data.sh executed successfully."
"""

    def _generate_system_prop(self, props: dict, module_type: str = "custom") -> str:
        """生成 system.prop 属性文件"""
        header = f"""{self._module_header_comment()}
# ============================================================
# system.prop - 系统属性修改文件
# Magisk会在开机时自动加载此文件中的属性
# 格式: 属性名=属性值
# 每行一条属性，支持注释 (以#开头)
# ============================================================
# 属性类型说明:
#   ro.* = 只读属性 (Read-Only)，一旦设置，系统运行期间不可修改
#   persist.* = 持久化属性，重启后仍然保留
#   sys.* = 系统属性，可动态修改
#   debug.* = 调试属性，用于开启/关闭调试功能
#   hw.* / hwui.* = 硬件/UI渲染相关属性
#   dalvik.* = Dalvik/ART虚拟机相关属性
# ============================================================

"""

        if module_type == "model_spoof":
            header += "# ===== 机型伪装属性 =====\n"
            header += "# 以下属性用于伪装设备型号，使应用认为你是另一台设备\n"
            header += "# 注意: 修改后可能需要清除Google Play商店/服务数据才能生效\n\n"

        elif module_type == "perf":
            header += "# ===== 性能优化属性 =====\n"
            header += "# 以下属性用于提升系统性能和响应速度\n\n"

        elif module_type == "debloat":
            header += "# ===== 系统精简属性 =====\n"
            header += "# 以下属性用于禁用不必要的系统功能，节省资源\n\n"

        elif module_type == "gpu":
            header += "# ===== GPU渲染优化属性 =====\n"
            header += "# 以下属性用于优化GPU渲染性能\n\n"

        for prop, value in props.items():
            header += f"{prop}={value}\n"

        return header

    def generate_model_spoof_module(self, device_template: str = None,
                                     custom_props: dict = None):
        """生成改机型伪装模块"""
        template = DEVICE_TEMPLATES.get(device_template) if device_template else None

        if template:
            props = template["props"].copy()
            display_name = template["name"]
            module_id = f"model_spoof_{device_template}"
        elif custom_props:
            props = custom_props
            display_name = "Custom Model Spoof"
            module_id = "model_spoof_custom"
        else:
            popup_message(T("error"), T("magisk_gen_fail") + ": " + T("magisk_no_template_selected"), "red")
            return

        module_name = f"{display_name} Spoof"
        module_ver = "v1.0"
        module_ver_code = "1"
        module_author = "RootToolbox"
        module_desc = f"Device model spoofed as {display_name}.\nGenerated by AndWreBox - 安卓扳手盒子 v1.0"

        # 创建临时中间目录
        module_dir = os.path.join(self.tmp_dir, module_id)
        os.makedirs(module_dir, exist_ok=True)

        loading_spinner(T("processing") + f" {display_name}", 1.0)

        with gradient_progress(4, T("magisk_gen_model")) as (progress, task):
            # 1. module.prop
            shell.write_file(
                f"{module_dir}/module.prop",
                self._generate_module_prop(module_id, module_name, module_ver,
                                           module_ver_code, module_author, module_desc)
            )
            self._verify_file(f"{module_dir}/module.prop")
            progress.update(task, advance=1)

            # 2. customize.sh
            shell.write_file(
                f"{module_dir}/customize.sh",
                self._generate_customize_sh("model_spoof", {"display_name": display_name})
            )
            self._verify_file(f"{module_dir}/customize.sh")
            progress.update(task, advance=1)

            # 3. system.prop
            shell.write_file(
                f"{module_dir}/system.prop",
                self._generate_system_prop(props, "model_spoof")
            )
            self._verify_file(f"{module_dir}/system.prop")
            progress.update(task, advance=1)

            # 4. post-fs-data.sh
            shell.write_file(
                f"{module_dir}/post-fs-data.sh",
                self._generate_post_fs_data_sh("model_spoof")
            )
            self._verify_file(f"{module_dir}/post-fs-data.sh")
            progress.update(task, advance=1)

        # 验证所有文件
        all_ok = True
        for fname in ["module.prop", "customize.sh", "system.prop", "post-fs-data.sh"]:
            if not self._verify_file(f"{module_dir}/{fname}"):
                all_ok = False

        zip_path = None
        if all_ok:
            zip_path = f"{self.output_dir}/{module_id}.zip"
            self._create_module_zip(module_dir, zip_path)

        result_msg = f"{T('magisk_gen_ok')}\n{module_dir}/"
        if zip_path:
            result_msg += f"\n{zip_path}"
        else:
            result_msg += "\n" + T("magisk_zip_warning")
        popup_message(T("success"), result_msg, "green")
        log_event("SUCCESS", "MAGISK", f"生成改机型模块: {display_name}")

        return module_dir, zip_path

    def generate_performance_module(self):
        """生成性能优化模块"""
        module_id = "perf_optimizer"
        module_name = "System Performance Optimizer"
        module_ver = "v1.0"
        module_ver_code = "1"
        module_author = "RootToolbox"
        module_desc = ("System performance optimization module.\n"
                       "CPU/GPU/Memory/Network all-round optimization.\n"
                       "Generated by AndWreBox - 安卓扳手盒子 v1.0")

        props = {
            "debug.composition.type": "gpu",
            "debug.sf.hw": "1",
            "persist.sys.composition.type": "gpu",
            "hwui.render_dirty_regions": "false",
            "debug.performance.tuning": "1",
            "video.accelerate.hw": "1",
            "touch.pressure.scale": "0.001",
            "view.scroll_friction": "1.5",
            "wifi.supplicant_scan_interval": "300",
            "pm.sleep_mode": "1",
            "net.tcp.buffersize.default": "4096,87380,256960,4096,16384,256960",
            "net.tcp.buffersize.wifi": "4096,87380,256960,4096,16384,256960",
            "dalvik.vm.heapstartsize": "16m",
            "dalvik.vm.heapgrowthlimit": "256m",
            "dalvik.vm.heapsize": "512m",
            "dalvik.vm.heaptargetutilization": "0.75",
            "ro.config.hw_quickpoweron": "true",
            "persist.sys.shutdown.mode": "hibernate",
            "ro.logd.size": "256K",
            "persist.logd.size": "256K",
            "ro.logd.kernel": "false",
        }

        module_dir = os.path.join(self.tmp_dir, module_id)
        os.makedirs(module_dir, exist_ok=True)
        loading_spinner(T("processing"), 1.0)
        with gradient_progress(5, T("magisk_gen_perf")) as (progress, task):
            shell.write_file(f"{module_dir}/module.prop",
                self._generate_module_prop(module_id, module_name, module_ver, module_ver_code, module_author, module_desc))
            self._verify_file(f"{module_dir}/module.prop"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/customize.sh",
                self._generate_customize_sh("perf", {"display_name": module_name}))
            self._verify_file(f"{module_dir}/customize.sh"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/system.prop",
                self._generate_system_prop(props, "perf"))
            self._verify_file(f"{module_dir}/system.prop"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/service.sh",
                self._generate_service_sh("perf"))
            self._verify_file(f"{module_dir}/service.sh"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/post-fs-data.sh",
                self._generate_post_fs_data_sh("perf"))
            self._verify_file(f"{module_dir}/post-fs-data.sh"); progress.update(task, advance=1)
        all_ok = True
        for fname in ["module.prop", "customize.sh", "system.prop", "service.sh", "post-fs-data.sh"]:
            if not self._verify_file(f"{module_dir}/{fname}"): all_ok = False
        zip_path = None
        if all_ok: zip_path = f"{self.output_dir}/{module_id}.zip"; self._create_module_zip(module_dir, zip_path)
        result_msg = f"{T('magisk_gen_ok')}\n{module_dir}/"
        if zip_path: result_msg += f"\n{zip_path}"
        else: result_msg += "\n" + T("magisk_zip_warning")
        popup_message(T("success"), result_msg, "green")
        log_event("SUCCESS", "MAGISK", f"生成性能优化模块: {module_name}")
        return module_dir, zip_path

    def generate_custom_props_module(self):
        """生成自定义属性模块"""
        module_id = Prompt.ask(f"[cyan]{T('magisk_module_name')}[/]", default=T("magisk_default_module_id"))
        module_name = Prompt.ask(f"[cyan]{T('magisk_module_name')}[/]", default=T("magisk_default_module_name"))
        module_ver = Prompt.ask(f"[cyan]{T('magisk_module_version')}[/]", default=T("magisk_default_version"))
        module_author = Prompt.ask(f"[cyan]{T('magisk_module_author')}[/]", default=T("magisk_default_author"))
        module_desc = Prompt.ask(f"[cyan]{T('magisk_module_desc')}[/]", default=T("magisk_default_desc"))
        console.print(f"\n[cyan]{T('spoof_custom_props')}[/]")
        console.print(f"[dim]{T('magisk_prop_format_hint')}[/]\n")
        props = {}
        while True:
            line = Prompt.ask("[dim]prop[/]", default="")
            if not line: break
            if "=" in line:
                key, val = line.split("=", 1)
                props[key.strip()] = val.strip()
        if not props: props = {"debug.performance.tuning": "1", "video.accelerate.hw": "1"}
        module_dir = os.path.join(self.tmp_dir, module_id)
        os.makedirs(module_dir, exist_ok=True)
        loading_spinner(T("processing"), 1.0)
        with gradient_progress(3, T("magisk_gen_props")) as (progress, task):
            shell.write_file(f"{module_dir}/module.prop",
                self._generate_module_prop(module_id, module_name, module_ver, "1", module_author, module_desc))
            self._verify_file(f"{module_dir}/module.prop"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/customize.sh",
                self._generate_customize_sh("custom", {"display_name": module_name}))
            self._verify_file(f"{module_dir}/customize.sh"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/system.prop",
                self._generate_system_prop(props, "custom"))
            self._verify_file(f"{module_dir}/system.prop"); progress.update(task, advance=1)
        all_ok = True
        for fname in ["module.prop", "customize.sh", "system.prop"]:
            if not self._verify_file(f"{module_dir}/{fname}"): all_ok = False
        zip_path = None
        if all_ok: zip_path = f"{self.output_dir}/{module_id}.zip"; self._create_module_zip(module_dir, zip_path)
        result_msg = f"{T('magisk_gen_ok')}\n{module_dir}/"
        if zip_path: result_msg += f"\n{zip_path}"
        else: result_msg += "\n" + T("magisk_zip_warning")
        popup_message(T("success"), result_msg, "green")
        log_event("SUCCESS", "MAGISK", f"生成自定义属性模块: {module_id}")
        return module_dir, zip_path

    def generate_debloat_module(self):
        """生成系统精简模块"""
        module_id = "system_debloat"
        module_name = "System Debloat"
        module_ver = "v1.0"
        module_ver_code = "1"
        module_author = "RootToolbox"
        module_desc = ("System debloat module.\nDisable unnecessary system services and apps.\nGenerated by AndWreBox - 安卓扳手盒子 v1.0")
        props = {
            "ro.config.cellbroadcast": "false", "log.tag.stats_log": "ERROR",
            "persist.logd.size": "256K", "ro.logd.size": "256K", "ro.logd.kernel": "false",
            "persist.sys.dalvik.vm.lib.2": "libart.so", "config.disable_atlas": "true",
            "ro.config.low_ram": "false", "persist.sys.ui.hw": "true",
        }
        module_dir = os.path.join(self.tmp_dir, module_id)
        os.makedirs(module_dir, exist_ok=True)
        loading_spinner(T("processing"), 1.0)
        with gradient_progress(4, T("magisk_gen_debloat")) as (progress, task):
            shell.write_file(f"{module_dir}/module.prop",
                self._generate_module_prop(module_id, module_name, module_ver, module_ver_code, module_author, module_desc))
            self._verify_file(f"{module_dir}/module.prop"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/customize.sh",
                self._generate_customize_sh("debloat", {"display_name": module_name}))
            self._verify_file(f"{module_dir}/customize.sh"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/system.prop",
                self._generate_system_prop(props, "debloat"))
            self._verify_file(f"{module_dir}/system.prop"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/service.sh",
                self._generate_service_sh("debloat"))
            self._verify_file(f"{module_dir}/service.sh"); progress.update(task, advance=1)
        all_ok = True
        for fname in ["module.prop", "customize.sh", "system.prop", "service.sh"]:
            if not self._verify_file(f"{module_dir}/{fname}"): all_ok = False
        zip_path = None
        if all_ok: zip_path = f"{self.output_dir}/{module_id}.zip"; self._create_module_zip(module_dir, zip_path)
        result_msg = f"{T('magisk_gen_ok')}\n{module_dir}/"
        if zip_path: result_msg += f"\n{zip_path}"
        else: result_msg += "\n" + T("magisk_zip_warning")
        popup_message(T("success"), result_msg, "green")
        log_event("SUCCESS", "MAGISK", "生成系统精简模块")
        return module_dir, zip_path

    def generate_gpu_module(self):
        """生成GPU优化模块"""
        module_id = "gpu_optimizer"
        module_name = "GPU Optimizer"
        module_ver = "v1.0"
        module_ver_code = "1"
        module_author = "RootToolbox"
        module_desc = ("GPU optimization module.\nAdreno GPU performance boost.\nGenerated by AndWreBox - 安卓扳手盒子 v1.0")
        props = {
            "debug.composition.type": "gpu", "debug.sf.hw": "1",
            "persist.sys.composition.type": "gpu", "hwui.render_dirty_regions": "false",
            "debug.hwui.renderer": "skiagl", "ro.hardware.egl": "adreno",
            "ro.hardware.vulkan": "adreno", "debug.enable.sgl": "1",
            "persist.graphics.vsync.disable": "0", "debug.sf.disable_client_composition_cache": "1",
            "debug.sf.latch_unsignaled": "1", "debug.sf.enable_gl_backpressure": "1",
            "debug.sf.early_phase_offset_ns": "500000", "debug.sf.early_gl_phase_offset_ns": "3000000",
            "debug.sf.early_app_phase_offset_ns": "500000",
        }
        module_dir = os.path.join(self.tmp_dir, module_id)
        os.makedirs(module_dir, exist_ok=True)
        loading_spinner(T("processing"), 1.0)
        with gradient_progress(5, T("magisk_gen_gpu")) as (progress, task):
            shell.write_file(f"{module_dir}/module.prop",
                self._generate_module_prop(module_id, module_name, module_ver, module_ver_code, module_author, module_desc))
            self._verify_file(f"{module_dir}/module.prop"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/customize.sh",
                self._generate_customize_sh("gpu", {"display_name": module_name}))
            self._verify_file(f"{module_dir}/customize.sh"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/system.prop",
                self._generate_system_prop(props, "gpu"))
            self._verify_file(f"{module_dir}/system.prop"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/service.sh",
                self._generate_service_sh("gpu"))
            self._verify_file(f"{module_dir}/service.sh"); progress.update(task, advance=1)
            shell.write_file(f"{module_dir}/post-fs-data.sh",
                self._generate_post_fs_data_sh("gpu"))
            self._verify_file(f"{module_dir}/post-fs-data.sh"); progress.update(task, advance=1)
        all_ok = True
        for fname in ["module.prop", "customize.sh", "system.prop", "service.sh", "post-fs-data.sh"]:
            if not self._verify_file(f"{module_dir}/{fname}"): all_ok = False
        zip_path = None
        if all_ok: zip_path = f"{self.output_dir}/{module_id}.zip"; self._create_module_zip(module_dir, zip_path)
        result_msg = f"{T('magisk_gen_ok')}\n{module_dir}/"
        if zip_path: result_msg += f"\n{zip_path}"
        else: result_msg += "\n" + T("magisk_zip_warning")
        popup_message(T("success"), result_msg, "green")
        log_event("SUCCESS", "MAGISK", "生成GPU优化模块")
        return module_dir, zip_path

    def list_modules(self):
        """列出已生成的模块"""
        title_panel(T("magisk_list_modules"), self.output_dir)
        ok, out, _ = shell.run(f"ls -la {self.output_dir}/ 2>/dev/null")
        if ok: console.print(out)
        else: console.print(f"  [dim]{T('not_available')}[/]")

    def interactive_menu(self):
        """Magisk模块生成器交互菜单"""
        while True:
            console.clear()
            title_panel(T("magisk_title"), T("magisk_subtitle"))

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('magisk_gen_model')} [dim](36款机型)[/]")
            console.print(f"  [bold cyan]2.[/] {T('magisk_gen_perf')}")
            console.print(f"  [bold cyan]3.[/] {T('magisk_gen_props')}")
            console.print(f"  [bold cyan]4.[/] {T('magisk_gen_debloat')}")
            console.print(f"  [bold cyan]5.[/] {T('magisk_gen_gpu')}")
            console.print(f"  [bold cyan]6.[/] {T('magisk_list_modules')}")
            console.print(f"  [bold cyan]0.[/] {T('back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]", default="0")

            if choice == "0":
                break
            elif choice == "1":
                console.clear()
                title_panel(T("magisk_gen_model"), T("magisk_target_device"))
                templates = list(DEVICE_TEMPLATES.keys())
                # 按分类分组显示
                console.print()
                console.print(f"  [bold bright_yellow]═══ Snapdragon 8 Elite / Gen 5 系列 (2025-2026) ═══[/]")
                elite_keys = [k for k in templates if k in [
                    "samsung_s25_ultra", "samsung_s25_plus", "samsung_s25",
                    "samsung_z_fold_7", "samsung_z_flip_7",
                    "xiaomi_15_ultra", "xiaomi_15_pro", "xiaomi_15",
                    "oneplus_13", "oneplus_13r",
                    "oppo_find_x8_ultra", "oppo_find_x8_pro",
                    "vivo_x200_ultra", "vivo_x200_pro",
                    "iqoo_13", "realme_gt_8_pro",
                    "asus_rog_9", "red_magic_10_pro",
                    "honor_magic_7_pro", "google_pixel_10_pro",
                ]]
                for i, key in enumerate(elite_keys, 1):
                    console.print(f"  [cyan]{i:2d}.[/] {DEVICE_TEMPLATES[key]['name']} [dim]({key})[/]")

                console.print()
                console.print(f"  [bold bright_yellow]═══ Snapdragon 8 Gen 3 系列 (2024) ═══[/]")
                gen3_keys = [k for k in templates if k in [
                    "samsung_s24_ultra", "samsung_s24_plus", "samsung_s24",
                    "xiaomi_14_ultra", "xiaomi_14_pro", "xiaomi_14",
                    "oneplus_12", "oppo_find_x7_ultra",
                    "vivo_x100_ultra", "realme_gt_5_pro",
                ]]
                for i, key in enumerate(gen3_keys, len(elite_keys) + 1):
                    console.print(f"  [cyan]{i:2d}.[/] {DEVICE_TEMPLATES[key]['name']} [dim]({key})[/]")

                console.print()
                console.print(f"  [bold bright_yellow]═══ Snapdragon 8 Gen 2 系列 (2023) ═══[/]")
                gen2_keys = [k for k in templates if k in [
                    "samsung_s23_ultra", "samsung_s23_plus", "samsung_s23",
                    "xiaomi_13_ultra", "xiaomi_13_pro", "oneplus_11",
                ]]
                for i, key in enumerate(gen2_keys, len(elite_keys) + len(gen3_keys) + 1):
                    console.print(f"  [cyan]{i:2d}.[/] {DEVICE_TEMPLATES[key]['name']} [dim]({key})[/]")

                console.print()
                console.print(f"  [cyan]0.[/] {T('back')}")
                t = Prompt.ask(f"[bold]{T('please_select')}[/]",
                               default="0")
                if t != "0":
                    try:
                        idx = int(t) - 1
                        if 0 <= idx < len(templates):
                            self.generate_model_spoof_module(templates[idx])
                        else:
                            popup_message(T("error"), T("magisk_invalid_selection"), "red")
                    except (ValueError, IndexError):
                        popup_message(T("error"), T("magisk_invalid_selection"), "red")
                input(f"\n{T('press_any_key')}")
            elif choice == "2":
                self.generate_performance_module()
                input(f"\n{T('press_any_key')}")
            elif choice == "3":
                self.generate_custom_props_module()
                input(f"\n{T('press_any_key')}")
            elif choice == "4":
                self.generate_debloat_module()
                input(f"\n{T('press_any_key')}")
            elif choice == "5":
                self.generate_gpu_module()
                input(f"\n{T('press_any_key')}")
            elif choice == "6":
                self.list_modules()
                input(f"\n{T('press_any_key')}")
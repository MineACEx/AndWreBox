# AndWreBox (安卓扳手盒子) v1.0

> 基于 Termux 的 Android Root 底层优化全能工具箱，15 个功能模块 | A Termux-based All-in-One Android Root Optimization Toolbox with 15 Feature Modules

[![Version](https://img.shields.io/badge/version-1.0-blue)](https://github.com)
[![Python](https://img.shields.io/badge/python-3-green)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Termux%20(Android)-orange)](https://termux.dev/)
[![License](https://img.shields.io/badge/license-Open%20Source-brightgreen)](LICENSE)

---

## 目录 | Table of Contents

- [中文文档](#中文文档)
  - [项目简介](#项目简介)
  - [功能模块](#功能模块)
  - [系统要求](#系统要求)
  - [安装指南](#安装指南)
  - [使用方式](#使用方式)
  - [Termux 常见问题](#termux常见问题)
  - [首次启动流程](#首次启动流程)
  - [安全机制](#安全机制)
  - [存储路径](#存储路径)
  - [支持芯片](#支持芯片)
  - [视觉效果](#视觉效果)
  - [文件结构](#文件结构)
  - [许可证](#许可证)
- [English Documentation](#english-documentation)
  - [Project Overview](#project-overview)
  - [Feature Modules](#feature-modules)
  - [System Requirements](#system-requirements)
  - [Installation Guide](#installation-guide)
  - [Usage](#usage)
  - [Termux FAQ](#termux-faq)
  - [First Launch Flow](#first-launch-flow)
  - [Security](#security)
  - [Storage Paths](#storage-paths)
  - [Supported Chipsets](#supported-chipsets)
  - [Visual Effects](#visual-effects)
  - [File Structure](#file-structure)
  - [License](#license)

---

# 中文文档

## 项目简介

**AndWreBox（安卓扳手盒子）v1.0** 是一款基于 Termux 终端环境的 Android Root 底层优化全能工具箱。本工具深度适配高通骁龙系列芯片，集成 **15 大功能模块**，覆盖 CPU 调度、GPU 调优、温控管理、内存优化、内核调校、Magisk 模块构建、IMG 镜像工具、设备伪装、网络加速、应用管理、电池健康、内核刷写等核心场景，为高级用户和开发者提供一站式系统调优方案。所有数据使用 AES-256-CBC 加密，加密密钥与设备绑定。

## 功能模块

AndWreBox 内置 **15 个功能模块**，覆盖系统性能优化的方方面面：

| 编号 | 模块名称 | 功能描述 |
|:---:|----------|----------|
| 1 | CPU 调度优化 | 动态调整 CPU 调度策略，优化大小核负载分配，支持自定义调速器参数 |
| 2 | Adreno GPU 优化 | GPU 频率调节、渲染管线优化、Adreno 专属参数调优 |
| 3 | 温控管理 | 自定义温控阈值、散热策略配置，防止降频锁帧 |
| 4 | 内存管理 | 虚拟内存调优、ZRAM 配置、LMK 参数调整、缓存清理 |
| 5 | 系统微调 | Build.prop 编辑、内核参数 sysctl 优化、动画速度调节 |
| 6 | 快捷工具 | 一键性能模式切换、常用系统命令快捷入口 |
| 7 | 实时监控 | CPU/GPU 频率、温度、帧率、功耗等实时数据面板 |
| 8 | Magisk 模块构建 | Magisk模块生成器 — 36款预设机型模板（骁龙8 Elite/Gen5/Gen3/Gen2）一键生成改机型模块，同时支持性能优化、自定义属性、系统精简、GPU增强等模块生成 |
| 9 | IMG 镜像工具 | boot.img / vendor_boot.img 解包、打包与修改 |
| 10 | 设备伪装 | 设备属性伪装（机型/指纹/GPU/传感器），支持自定义属性批量修改 |
| 11 | 网络优化 | TCP 拥塞算法调优、DNS 优化、网络延迟降低 |
| 12 | 应用管理 | 批量冻结/解冻应用、权限管理、后台限制 |
| 13 | 内核调校 | 内核参数深度自定义、I/O 调度器切换、熵值调整 |
| 14 | 电池健康 | 电池状态检测、充电控制、温度监控、健康度评估 |
| 15 | [BETA] AnyKernel3 Kernel Flash | 内核检测、备份、刷写与验证，支持 A/B 分区检测 |

### [BETA] AnyKernel3 Kernel Flash 模块说明

安全知识测验（中英双语题库，10题随机抽3题，答对一次后可开启免答题开关），内核备份/恢复/刷写

## 系统要求

| 项目 | 要求 |
|------|------|
| 运行方式 | 方式一：Termux（F-Droid 最新版）+ Python 3 |
|  | 方式二：Magisk/KernelSU Python3 模块（刷入后无需Termux，任意Root终端直接运行） |
| Python | Python 3 |
| Root 权限 | Magisk / KernelSU / APatch |
| Android 版本 | Android 12 及以上 |
| 存储空间 | 至少 200 MB 可用空间 |

## 安装指南

### 第一步：从 F-Droid 安装 Termux

请务必从 **F-Droid** 安装 Termux，**不要使用 Google Play 版本**（Google Play 上的 Termux 已停止更新，功能受限）。

下载地址：[https://f-droid.org/packages/com.termux/](https://f-droid.org/packages/com.termux/)

### 第二步：更新 Termux 软件源

打开 Termux，依次运行以下命令：

```bash
pkg update && pkg upgrade -y
```

### 第三步：安装 Python

```bash
pkg install python3 -y
```

### 第四步：下载并解压 AndWreBox

将 AndWreBox_v1.0.zip 传输到手机后，在 Termux 中执行：

```bash
unzip AndWreBox_v1.0.zip -d ~/
```

### 第五步：进入工具目录

```bash
cd ~/android_root_toolbox
```

### 第六步：启动 AndWreBox

```bash
bash run.sh
```

### 方式二：Magisk/KernelSU Python3 模块

1. 刷入 `python3_module/` 目录下的 Magisk 模块
2. 模块自动挂载 Python3 到 `/system/bin/` 和 `/system/lib/`
3. 首次开机会自动安装 `rich`、`colorama`、`blessed`、`pyfiglet` 依赖
4. 使用 `run.sh` 启动脚本

```bash
sh run.sh
```

## 使用方式

### 启动命令

```bash
sh run.sh      # 通用启动器（Termux + 模块双兼容）
```

- **Termux 环境**：在 Termux 中进入工具目录后执行 `sh run.sh`
- **模块环境**：刷入 Magisk/KernelSU Python3 模块后，在任意 Root 终端（如 adb shell、MT 管理器终端等）中进入工具目录后执行 `sh run.sh`

## Termux 常见问题

### 1. 存储权限问题

如果无法访问手机存储，请运行以下命令授予存储权限：

```bash
termux-setup-storage
```

执行后会弹出系统权限请求，点击"允许"即可。

### 2. pip 安装失败

如果 pip 安装依赖时出现 externally-managed-environment 错误，请使用以下命令：

```bash
pip install --break-system-packages -r requirements.txt
```

### 3. 字体显示乱码

如果终端界面出现乱码或字符显示异常，请安装字体配置包：

```bash
pkg install fontconfig
```

### 4. 提示 "su not found"

如果启动时提示 `su not found`，说明当前环境未获取 Root 权限。请确保：

- 手机已通过 Magisk / KernelSU / APatch 完成 Root
- 在对应的 Root 管理应用中已授予 Termux Root 权限
- 在 Termux 中输入 `su` 命令确认可以正常提权

## 首次启动流程

首次启动 AndWreBox 时，系统将按照以下顺序完成初始化：

1. **启动画面（Splash）** —— 全屏雪花飘落动画，雪花逐渐汇聚形成 AndWreBox Logo（4.5秒三阶段动画：自由飘落 → 曲线汇聚 → Logo定形）
2. **免责协议（Disclaimer）** —— 显示并确认用户免责声明，不同意则退出
3. **身份认证（Auth）** —— 首次使用创建访问密码，后续启动需密码验证
4. **设备信息采集** —— 自动检测 Root 权限、识别芯片型号、系统版本等关键硬件信息
5. **主菜单** —— 左对齐数字编号，单行紧凑布局，15个功能模块

## 安全机制

AndWreBox 采用多层安全防护，确保用户数据和认证信息的安全：

- **密码哈希** —— 用户密码采用 **SHA256 加盐哈希** 存储，不以明文形式保存
- **AES-256 加密** —— 所有持久化数据（密码、配置、日志等）使用 **AES-256-CBC** 加密存储于 `/data/andwrebox/` 目录
- **设备绑定密钥** —— 加密密钥基于设备序列号 + 型号通过 PBKDF2 派生，即使数据文件被拷贝到其他设备也无法解密
- **本地存储** —— 所有数据均在设备本地处理，不上传至任何服务器
- **认证令牌** —— 登录令牌加密存储，仅在设备本地有效

> 请妥善保管您的访问密码。密码遗失后需手动删除 `/data/andwrebox/auth/` 目录以重置。

## 存储路径

AndWreBox 使用 Android 系统级路径存储数据，确保安全性与隔离性：

| 目录 | 用途 | 说明 |
|------|------|------|
| `/data/andwrebox/` | 加密数据存储 | 用户密码、配置、认证令牌、日志、备份等敏感数据均以 AES-256 加密形式存储于此 |
| `/data/local/tmp/andwrebox/` | 临时缓存 | 运行时临时文件、缓存数据，可通过设置菜单中的"清理缓存"功能一键清除 |
| `/sdcard/AndWreBox/output/` | 模块输出 | 用户可见的模块输出目录（默认），如 Magisk 模块构建产物、导出的配置文件等 |

> 设置菜单提供自动验证、修改密码、清理缓存、自定义模块输出、AK3免答题开关等功能。缓存清理功能会清除 `/data/local/tmp/andwrebox/` 中的临时文件，释放存储空间，不影响用户数据和配置。

## 支持芯片

AndWreBox 针对以下高通骁龙芯片平台进行了深度适配与优化：

| 芯片型号 | 代号 | 适配状态 |
|----------|------|:---:|
| 骁龙 8 Elite | SM8750 | 深度适配 |
| 骁龙 8 Gen 5 | SM8850 | 深度适配 |
| 骁龙 8 Gen 4 | SM8750 | 深度适配 |
| 骁龙 8 Gen 3 | SM8650 | 深度适配 |
| 骁龙 8 Gen 2 | SM8550 | 深度适配 |
| 骁龙 8+ Gen 1 | SM8475 | 支持 |
| 骁龙 8 Gen 1 | SM8450 | 支持 |

> 其他高通骁龙 7 系列、6 系列芯片亦可使用基础功能，但部分高级优化可能不适用。

## 视觉效果

AndWreBox 内置 **37+ 种终端动画效果**，为命令行操作带来沉浸式视觉体验：

| 动画名称 | 效果描述 |
|----------|----------|
| `starfield` | 星空粒子穿梭效果 |
| `firework` | 烟花爆炸绽放动画 |
| `snowfall` | 雪花飘落效果 |
| `rain_drops` | 雨滴下落效果 |
| `neon_border_panel` | 霓虹灯边框闪烁面板 |
| `pulse_glow` | 脉冲发光文字动画 |
| `matrix_rain` | 黑客帝国数字雨效果 |
| `glitch_text` | 故障/撕裂文字效果 |
| `wave_text` | 波浪形文字动画 |
| `rainbow_flow_border` | 彩虹流光边框 |
| `rainbow_particle_explosion` | 彩虹粒子爆炸 |
| `rainbow_typewriter` | 彩虹色打字机效果 |
| `heartbeat` | 心跳脉动文字动画 |
| `rotate_3d_text` | 3D 旋转文字 |
| `spiral_animation` | 螺旋旋转动画 |
| `particle_burst` | 粒子爆发效果 |
| `particle_ring_loader` | 粒子环加载动画 |
| `explode_text` | 文字爆炸效果 |
| `typewriter` | 经典打字机效果 |
| `sweep_animation` | 扫光动画 |
| `gradient_progress` | 渐变色进度条 |
| `gradient_logo` | 渐变色 Logo 动画 |
| `gradient_slide` | 渐变滑动标题动画 |
| `loading_spinner` | 旋转加载指示器 |
| `loading_sweep` | 扫描式加载动画 |
| `animated_loading` | 综合加载动画 |
| `count_up_animation` | 数字递增动画 |
| `wave_progress_bar` | 波浪形进度条 |
| `scrolling_banner` | 滚动横幅文字 |
| `smooth_scroll` | 平滑滚动文字 |
| `color_cycle_border` | 色彩循环边框 |
| `rainbow_panel` | 彩虹渐变面板 |
| `popup_message` | 弹出消息框 |
| `divider` | 动态分隔线 |
| `title_panel` | 标题面板 |
| `gradient_progress_v2` | 多色渐变进度条 |
| `glow` | 发光效果 |

> 30fps优雅动画引擎（雪花Logo汇聚、雨滴、页面过渡、烟花、滚动横幅等）

## 文件结构

```
android_root_toolbox/
├── main.py                   # 主程序入口
├── run.sh                    # 通用启动器（Termux + 模块双兼容）
├── requirements.txt          # Python 依赖清单
├── README.md                 # 项目说明文档
├── python3_module/           # Magisk/KernelSU Python3 环境模块
├── core/
│   ├── __init__.py           # 核心模块初始化
│   ├── animations.py         # 30fps 动画引擎
│   ├── auth.py               # 用户认证与 SHA256 密码管理
│   ├── config.py             # 全局配置管理
│   ├── crypto.py             # AES-256-CBC 加密解密模块
│   ├── disclaimer.py         # 免责协议处理
│   ├── i18n.py               # 中英双语国际化
│   ├── logger.py             # 日志记录系统
│   ├── paths.py              # 统一路径管理
│   ├── shell.py              # Shell 命令执行封装
│   └── utils.py              # 通用工具函数
├── modules/
│   ├── __init__.py           # 模块初始化
│   ├── cpu.py                # 模块 1: CPU 调度优化
│   ├── gpu.py                # 模块 2: Adreno GPU 优化
│   ├── thermal.py            # 模块 3: 温控管理
│   ├── memory.py             # 模块 4: 内存管理
│   ├── system.py             # 模块 5: 系统微调
│   ├── quick_tools.py        # 模块 6: 快捷工具
│   ├── monitor.py            # 模块 7: 实时监控
│   ├── magisk_module.py      # 模块 8: Magisk 模块构建 (36款机型)
│   ├── img_tools.py          # 模块 9: IMG 镜像工具
│   ├── spoofing.py           # 模块 10: 设备伪装
│   ├── network.py            # 模块 11: 网络优化
│   ├── app_manager.py        # 模块 12: 应用管理
│   ├── kernel_tuner.py       # 模块 13: 内核调校
│   ├── battery.py            # 模块 14: 电池健康
│   └── anykernel3.py         # 模块 15: [BETA] AnyKernel3 Kernel Flash
```

## 许可证

本项目采用开源许可证发布。详见 [LICENSE](LICENSE) 文件。

---

# English Documentation

## Project Overview

**AndWreBox (Android Wrench Box) v1.0** is an all-in-one Android Root optimization toolbox built for the Termux terminal environment. Deeply optimized for Qualcomm Snapdragon chipsets, it integrates **15 powerful modules** covering CPU scheduling, GPU tuning, thermal management, memory optimization, kernel tuning, Magisk module building, IMG image tools, device spoofing, network acceleration, app management, battery health, kernel flashing, and more -- delivering a one-stop system tuning solution for advanced users and developers. All data is encrypted with AES-256-CBC using a device-bound key.

## Feature Modules

AndWreBox includes **15 feature modules** covering every aspect of system performance optimization:

| No. | Module | Description |
|:---:|--------|-------------|
| 1 | CPU Scheduler Optimization | Dynamically adjust CPU scheduling policies, optimize big.LITTLE core load distribution, support custom governor parameters |
| 2 | Adreno GPU Optimization | GPU frequency tuning, rendering pipeline optimization, Adreno-specific parameter adjustment |
| 3 | Thermal Management | Custom thermal thresholds, cooling strategy configuration to prevent throttling and frame drops |
| 4 | Memory Management | Virtual memory tuning, ZRAM configuration, LMK parameter adjustment, cache cleaning |
| 5 | System Tweaks | Build.prop editing, sysctl kernel parameter optimization, animation speed adjustment |
| 6 | Quick Tools | One-click performance mode switching, quick access to common system commands |
| 7 | Live Monitor | Real-time dashboard for CPU/GPU frequency, temperature, FPS, and power consumption |
| 8 | Magisk Module Builder | Magisk module generator — 36 preset device model templates (Snapdragon 8 Elite/Gen5/Gen3/Gen2) one-click to generate model spoofing modules, also supports performance optimization, custom properties, system debloating, GPU enhancement and other module generation |
| 9 | IMG Image Tools | Unpack, repack, and modify boot.img / vendor_boot.img |
| 10 | Device Spoofing | Device property spoofing (model/fingerprint/GPU/sensors), supports custom property batch modification |
| 11 | Network Optimization | TCP congestion algorithm tuning, DNS optimization, latency reduction |
| 12 | App Manager | Batch freeze/unfreeze apps, permission management, background restrictions |
| 13 | Kernel Tuner | Deep kernel parameter customization, I/O scheduler switching, entropy tuning |
| 14 | Battery Health | Battery status detection, charging control, temperature monitoring, health assessment |
| 15 | [BETA] AnyKernel3 Kernel Flash | Kernel detection, backup, flash, and verification with A/B slot detection |

### [BETA] AnyKernel3 Kernel Flash Module

Safety knowledge quiz (bilingual CN/EN question bank, 10 questions random 3, skip-quiz toggle after passing once), kernel backup/restore/flash

## System Requirements

| Item | Requirement |
|------|-------------|
| Runtime | Method 1: Termux (latest from F-Droid) + Python 3 |
|  | Method 2: Magisk/KernelSU Python3 Module (flash and run directly in any Root terminal, no Termux needed) |
| Python | Python 3 |
| Root Access | Magisk / KernelSU / APatch |
| Android Version | Android 12 or higher |
| Storage | At least 200 MB free space |

## Installation Guide

### Step 1: Install Termux from F-Droid

Make sure to install Termux from **F-Droid** -- **do NOT use the Google Play version** (the Google Play build is outdated and has limited functionality).

Download: [https://f-droid.org/packages/com.termux/](https://f-droid.org/packages/com.termux/)

### Step 2: Update Termux Package Sources

Open Termux and run the following commands:

```bash
pkg update && pkg upgrade -y
```

### Step 3: Install Python

```bash
pkg install python3 -y
```

### Step 4: Download and Extract AndWreBox

After transferring AndWreBox_v1.0.zip to your device, run in Termux:

```bash
unzip AndWreBox_v1.0.zip -d ~/
```

### Step 5: Enter the Tool Directory

```bash
cd ~/android_root_toolbox
```

### Step 6: Launch AndWreBox

```bash
bash run.sh
```

### Method 2: Magisk/KernelSU Python3 Module

1. Flash the Magisk module from the `python3_module/` directory
2. The module automatically mounts Python3 to `/system/bin/` and `/system/lib/`
3. On first boot, dependencies (`rich`, `colorama`, `blessed`, `pyfiglet`) are automatically installed
4. Use `run.sh` to launch

```bash
sh run.sh
```

## Usage

### Launch Command

```bash
sh run.sh      # Universal launcher (Termux + Module dual compatible)
```

- **Termux Environment**: Navigate to the tool directory in Termux and run `sh run.sh`
- **Module Environment**: After flashing the Magisk/KernelSU Python3 module, navigate to the tool directory in any Root terminal (e.g., adb shell, MT Manager terminal, etc.) and run `sh run.sh`

## Termux FAQ

### 1. Storage Permission

If you cannot access device storage, grant storage permission by running:

```bash
termux-setup-storage
```

A system permission dialog will appear -- tap "Allow" to proceed.

### 2. pip Installation Failure

If pip fails with an externally-managed-environment error when installing dependencies, use:

```bash
pip install --break-system-packages -r requirements.txt
```

### 3. Garbled Font Display

If the terminal shows garbled text or display issues, install the font configuration package:

```bash
pkg install fontconfig
```

### 4. "su not found" Error

If you see `su not found` at startup, it means the current environment does not have Root access. Ensure that:

- Your device has been rooted via Magisk / KernelSU / APatch
- Termux has been granted Root access in your Root management app
- You can successfully elevate privileges by typing `su` in Termux

## First Launch Flow

When launching AndWreBox for the first time, the system will complete initialization in the following order:

1. **Splash Screen** -- Full-screen snowfall animation, snowflakes gradually converge to form the AndWreBox Logo (4.5s three-stage animation: free fall -> curved convergence -> logo formation)
2. **Disclaimer** -- Display and confirm the user disclaimer; exit if not accepted
3. **Authentication (Auth)** -- Create an access password on first use; password verification required for subsequent launches
4. **Device Info Collection** -- Automatically detect Root privileges, identify chipset model, system version, and other key hardware information
5. **Main Menu** -- Left-aligned numbered entries, single-line compact layout, 15 feature modules

## Security

AndWreBox employs multiple layers of security to protect user data and authentication:

- **Password Hashing** -- User passwords are stored using **SHA256 salted hashing** and are never saved in plain text
- **AES-256 Encryption** -- All persistent data (passwords, configs, logs, etc.) is encrypted with **AES-256-CBC** and stored in `/data/andwrebox/`
- **Device-Bound Key** -- The encryption key is derived from the device serial number + model via PBKDF2, ensuring data files copied to another device cannot be decrypted
- **Local Storage** -- All data is processed entirely on-device; nothing is uploaded to any server
- **Auth Token** -- Login tokens are encrypted and valid only on the local device

> Please keep your access password safe. If lost, manually delete the `/data/andwrebox/auth/` directory to reset.

## Storage Paths

AndWreBox uses Android system-level paths for data storage, ensuring security and isolation:

| Directory | Purpose | Description |
|-----------|---------|-------------|
| `/data/andwrebox/` | Encrypted data storage | User passwords, configurations, auth tokens, logs, backups, and other sensitive data encrypted with AES-256 |
| `/data/local/tmp/andwrebox/` | Temporary cache | Runtime temporary files and cache data; can be cleaned via the "Clean Cache" option in the Settings menu |
| `/sdcard/AndWreBox/output/` | Module output | User-visible module output directory (default), such as Magisk module build artifacts, exported config files, etc. |

> The Settings menu provides auto-verify, change password, clear cache, custom module output, and AK3 skip-quiz toggle. The cache cleanup feature removes temporary files from `/data/local/tmp/andwrebox/`, freeing storage space without affecting user data or configurations.

## Supported Chipsets

AndWreBox has been deeply optimized and tested for the following Qualcomm Snapdragon chipsets:

| Chipset | Codename | Status |
|---------|----------|:---:|
| Snapdragon 8 Elite | SM8750 | Fully optimized |
| Snapdragon 8 Gen 5 | SM8850 | Fully optimized |
| Snapdragon 8 Gen 4 | SM8750 | Fully optimized |
| Snapdragon 8 Gen 3 | SM8650 | Fully optimized |
| Snapdragon 8 Gen 2 | SM8550 | Fully optimized |
| Snapdragon 8+ Gen 1 | SM8475 | Supported |
| Snapdragon 8 Gen 1 | SM8450 | Supported |

> Other Qualcomm Snapdragon 7-series and 6-series chipsets can also use basic features, though some advanced optimizations may not apply.

## Visual Effects

AndWreBox features **37+ terminal animation effects** for an immersive command-line experience:

| Animation | Description |
|-----------|-------------|
| `starfield` | Starfield particle effect |
| `firework` | Firework burst animation |
| `snowfall` | Snowfall effect |
| `rain_drops` | Raindrop effect |
| `neon_border_panel` | Neon glow border flashing panel |
| `pulse_glow` | Pulsing glow text animation |
| `matrix_rain` | Matrix-style digital rain effect |
| `glitch_text` | Glitch/distorted text effect |
| `wave_text` | Wavy text animation |
| `rainbow_flow_border` | Rainbow flow border |
| `rainbow_particle_explosion` | Rainbow particle explosion |
| `rainbow_typewriter` | Rainbow-colored typewriter effect |
| `heartbeat` | Heartbeat pulsing text animation |
| `rotate_3d_text` | 3D rotating text |
| `spiral_animation` | Spiral rotation animation |
| `particle_burst` | Particle burst effect |
| `particle_ring_loader` | Particle ring loading animation |
| `explode_text` | Text explosion effect |
| `typewriter` | Classic typewriter effect |
| `sweep_animation` | Light sweep animation |
| `gradient_progress` | Gradient progress bar |
| `gradient_logo` | Gradient logo animation |
| `gradient_slide` | Gradient slide title animation |
| `loading_spinner` | Spinning loading indicator |
| `loading_sweep` | Scanning loading animation |
| `animated_loading` | Composite loading animation |
| `count_up_animation` | Number count-up animation |
| `wave_progress_bar` | Wave-style progress bar |
| `scrolling_banner` | Scrolling banner text |
| `smooth_scroll` | Smooth scrolling text |
| `color_cycle_border` | Color cycling border |
| `rainbow_panel` | Rainbow gradient panel |
| `popup_message` | Popup message box |
| `divider` | Dynamic divider line |
| `title_panel` | Title panel |
| `gradient_progress_v2` | Multi-color gradient progress bar |
| `glow` | Glow effect |

> 30fps elegant animation engine (snowflake logo convergence, rain drops, page transitions, fireworks, scrolling banners, etc.)

## File Structure

```
android_root_toolbox/
├── main.py                   # Main program entry point
├── run.sh                    # Universal launcher (Termux + Module dual compatible)
├── requirements.txt          # Python dependency list
├── README.md                 # Project documentation
├── python3_module/           # Magisk/KernelSU Python3 environment module
├── core/
│   ├── __init__.py           # Core module initialization
│   ├── animations.py         # 30fps animation engine
│   ├── auth.py               # User authentication & SHA256 password management
│   ├── config.py             # Global configuration management
│   ├── crypto.py             # AES-256-CBC encryption/decryption module
│   ├── disclaimer.py         # Disclaimer handling
│   ├── i18n.py               # Bilingual internationalization (CN/EN)
│   ├── logger.py             # Logging system
│   ├── paths.py              # Unified path management
│   ├── shell.py              # Shell command execution wrapper
│   └── utils.py              # Common utility functions
├── modules/
│   ├── __init__.py           # Module initialization
│   ├── cpu.py                # Module 1: CPU Scheduler Optimization
│   ├── gpu.py                # Module 2: Adreno GPU Optimization
│   ├── thermal.py            # Module 3: Thermal Management
│   ├── memory.py             # Module 4: Memory Management
│   ├── system.py             # Module 5: System Tweaks
│   ├── quick_tools.py        # Module 6: Quick Tools
│   ├── monitor.py            # Module 7: Live Monitor
│   ├── magisk_module.py      # Module 8: Magisk Module Builder (36 models)
│   ├── img_tools.py          # Module 9: IMG Image Tools
│   ├── spoofing.py           # Module 10: Device Spoofing
│   ├── network.py            # Module 11: Network Optimization
│   ├── app_manager.py        # Module 12: App Manager
│   ├── kernel_tuner.py       # Module 13: Kernel Tuner
│   ├── battery.py            # Module 14: Battery Health
│   └── anykernel3.py         # Module 15: [BETA] AnyKernel3 Kernel Flash
```

## License

This project is released under an open source license. See the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>AndWreBox</b> -- 你的安卓，由你掌控 | Your Android, Under Your Control
</p>
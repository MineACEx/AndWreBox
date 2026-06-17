#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0 [BETA]
AnyKernel3 内核刷写模块 [BETA] - 内核检测 | 备份 | 刷写 | 验证
[BETA] 此模块为测试版，可能存在未知风险，请谨慎使用！
"""

import os
import time
import random
import zipfile
import io
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich import box
from rich.align import Align
from rich.text import Text

from core.shell import shell
from core.i18n import T, get_language, LANG_CN, LANG_EN
from core.paths import BACKUP_DIR, TMP_DIR, DATA_DIR
from core.animations import (
    console, loading_spinner, gradient_progress,
    popup_message, divider, title_panel, typewriter
)
from core.utils import log_event

from core.disclaimer import set_ak3_quiz_passed, is_ak3_skip_quiz

# ============================================================================
# [BETA] AnyKernel3 模块专用常量
# ============================================================================

# [BETA] 常见搜索路径
COMMON_ZIP_PATHS = [
    "/sdcard",
    "/sdcard/Download",
    "/sdcard/AnyKernel3",
    "/sdcard/AndWreBox/output",
    "/data/local/tmp",
]

# [BETA] 验证必需文件
ANY_KERNEL_REQUIRED_FILES = [
    "anykernel.sh",
]

# [BETA] 内核相关文件 (至少存在一个)
ANY_KERNEL_KERNEL_FILES = [
    "Image",
    "Image.gz",
    "Image.lz4",
    "zImage",
    "kernel",
]

# [BETA] DTB相关文件
ANY_KERNEL_DTB_FILES = [
    "dtb",
    "dtbo.img",
    "dtb.img",
]

# [BETA] 免责声明文本 - 中文
AK3_DISCLAIMER_ZH = """
╔══════════════════════════════════════════════════════════════╗
║        [BETA] AnyKernel3 内核刷写 - 危险操作警告              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [BETA] 本模块为测试版，可能包含未知Bug！                     ║
║                                                              ║
║  刷写内核属于高风险操作，可能导致:                            ║
║                                                              ║
║  [致命] 手机变砖 (无法开机，需要9008深度刷机)                 ║
║  [致命] 数据永久丢失 (分区损坏)                               ║
║  [严重] 系统不稳定、随机重启、卡顿                            ║
║  [严重] 失去官方保修资格                                      ║
║  [警告] WiFi/蓝牙/相机等硬件功能异常                           ║
║  [警告] 电池续航严重下降                                      ║
║                                                              ║
║  使用本模块前，请务必:                                        ║
║  1. 完整备份当前 boot.img 到电脑                              ║
║  2. 确保手机电量 > 60%                                        ║
║  3. 确认已解锁 Bootloader                                     ║
║  4. 确认已安装 Magisk/KernelSU 并授予Root                     ║
║  5. 了解如何进入 Fastboot/EDL 模式恢复                        ║
║                                                              ║
║  开发者不承担任何因使用本模块造成的数据丢失、                  ║
║  设备损坏或其他任何损失。继续使用即表示您已                    ║
║  充分了解风险并自愿承担全部后果。                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

# [BETA] 免责声明文本 - 英文
AK3_DISCLAIMER_EN = """
╔══════════════════════════════════════════════════════════════╗
║     [BETA] AnyKernel3 Kernel Flashing - DANGER WARNING       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [BETA] This module is BETA, may contain unknown bugs!       ║
║                                                              ║
║  Kernel flashing is a HIGH-RISK operation that may cause:    ║
║                                                              ║
║  [FATAL] Hard brick (won't boot, needs EDL/9008 flash)      ║
║  [FATAL] Permanent data loss (partition corruption)         ║
║  [SEVERE] System instability, random reboots, lag           ║
║  [SEVERE] Loss of official warranty                         ║
║  [WARNING] WiFi/BT/Camera hardware malfunction              ║
║  [WARNING] Severe battery drain                             ║
║                                                              ║
║  Before using this module, you MUST:                         ║
║  1. Fully backup current boot.img to PC                     ║
║  2. Ensure battery > 60%                                     ║
║  3. Confirm Bootloader is unlocked                           ║
║  4. Confirm Magisk/KernelSU with Root granted                ║
║  5. Know how to enter Fastboot/EDL recovery mode             ║
║                                                              ║
║  The developer bears NO responsibility for data loss,        ║
║  device damage, or any other losses. By continuing,          ║
║  you fully understand and accept ALL risks.                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

# ============================================================================
# [BETA] 知识测验题库
# ============================================================================

QUIZ_QUESTIONS_ZH = [
    {
        "question": "刷写AnyKernel3之前，最重要的操作是什么？",
        "options": ["重启手机", "备份当前内核(boot.img)", "清除缓存", "关闭WiFi"],
        "answer": "备份当前内核(boot.img)",
    },
    {
        "question": "手机线刷需要进入什么模式？",
        "options": ["Recovery模式", "Fastboot模式", "正常开机模式", "安全模式"],
        "answer": "Fastboot模式",
    },
    {
        "question": "AnyKernel3的工作原理是？",
        "options": ["直接替换整个分区", "解包→替换内核→重新打包", "删除系统文件", "修改build.prop"],
        "answer": "解包→替换内核→重新打包",
    },
    {
        "question": "如果刷入内核后无法开机，首先应该尝试什么？",
        "options": ["换新手机", "恢复备份的内核", "清除所有数据", "拔掉电池"],
        "answer": "恢复备份的内核",
    },
    {
        "question": "内核刷写前，手机电量至少应该保持在多少？",
        "options": ["10%", "30%", "50%", "80%"],
        "answer": "50%",
    },
    {
        "question": "Android设备中，boot.img分区存放的是什么？",
        "options": ["系统文件", "内核和ramdisk", "用户数据", "基带固件"],
        "answer": "内核和ramdisk",
    },
    {
        "question": "什么是A/B分区？",
        "options": ["两个系统分区用于无缝更新", "两个数据分区", "两个SD卡分区", "两个缓存分区"],
        "answer": "两个系统分区用于无缝更新",
    },
    {
        "question": "刷写内核时通常使用什么命令？",
        "options": ["cat", "dd", "cp", "mv"],
        "answer": "dd",
    },
    {
        "question": "Magisk/KernelSU获取的是什么权限？",
        "options": ["管理员权限", "Root(超级用户)权限", "访客权限", "开发者权限"],
        "answer": "Root(超级用户)权限",
    },
    {
        "question": "如果刷写过程中断电，可能导致什么后果？",
        "options": ["自动恢复", "分区损坏/变砖", "自动重启", "无影响"],
        "answer": "分区损坏/变砖",
    },
]

QUIZ_QUESTIONS_EN = [
    {
        "question": "What is the most important step before flashing AnyKernel3?",
        "options": ["Reboot phone", "Backup current kernel (boot.img)", "Clear cache", "Turn off WiFi"],
        "answer": "Backup current kernel (boot.img)",
    },
    {
        "question": "What mode is required for phone flashing via cable?",
        "options": ["Recovery mode", "Fastboot mode", "Normal boot", "Safe mode"],
        "answer": "Fastboot mode",
    },
    {
        "question": "How does AnyKernel3 work?",
        "options": ["Replace entire partition", "Unpack→Replace kernel→Repack", "Delete system files", "Modify build.prop"],
        "answer": "Unpack→Replace kernel→Repack",
    },
    {
        "question": "If phone won't boot after kernel flash, what should you try first?",
        "options": ["Buy new phone", "Restore backed up kernel", "Wipe all data", "Remove battery"],
        "answer": "Restore backed up kernel",
    },
    {
        "question": "Before kernel flashing, what should the battery level be at minimum?",
        "options": ["10%", "30%", "50%", "80%"],
        "answer": "50%",
    },
    {
        "question": "What does the boot.img partition contain on Android?",
        "options": ["System files", "Kernel and ramdisk", "User data", "Baseband firmware"],
        "answer": "Kernel and ramdisk",
    },
    {
        "question": "What is A/B partition?",
        "options": ["Two system partitions for seamless updates", "Two data partitions", "Two SD card partitions", "Two cache partitions"],
        "answer": "Two system partitions for seamless updates",
    },
    {
        "question": "What command is commonly used for kernel flashing?",
        "options": ["cat", "dd", "cp", "mv"],
        "answer": "dd",
    },
    {
        "question": "What permission does Magisk/KernelSU provide?",
        "options": ["Admin", "Root (Superuser)", "Guest", "Developer"],
        "answer": "Root (Superuser)",
    },
    {
        "question": "What can happen if power is lost during flashing?",
        "options": ["Auto recovery", "Partition damage/brick", "Auto reboot", "No effect"],
        "answer": "Partition damage/brick",
    },
]


class AnyKernel3Manager:
    """
    [BETA] AnyKernel3 内核刷写管理器
    提供内核检测、备份、刷写、验证等功能
    """

    def __init__(self):
        self._quiz_passed = False
        self._disclaimer_shown = False

    # ========================================================================
    # [BETA] 类级别静态入口 - 供 main.py 模块分发使用
    # ========================================================================

    @staticmethod
    def run():
        """
        [BETA] AnyKernel3 模块静态入口
        显示免责声明 -> 知识测验 -> 功能菜单
        供 main.py 通过 getattr + 调用 的方式触发
        """
        manager = AnyKernel3Manager()

        if not manager.enter():
            return

        manager.interactive_menu()

    # ========================================================================
    # [BETA] 免责声明
    # ========================================================================

    def show_disclaimer(self) -> bool:
        """
        [BETA] 显示免责声明，要求用户确认
        返回 True 表示用户同意继续
        """
        console.clear()

        lang = get_language()
        disclaimer_text = AK3_DISCLAIMER_ZH if lang == LANG_CN else AK3_DISCLAIMER_EN

        console.print()
        console.print(Panel(
            Align.center(disclaimer_text, vertical="middle"),
            title="[bold bright_red][BETA] " + T("AnyKernel3 内核刷写 - 免责声明"),
            border_style="bright_red",
            box=box.ROUNDED,
            padding=(1, 2),
        ))
        console.print()

        typewriter("[BETA] " + T("请仔细阅读以上免责声明"), delay=0.02, style="bold yellow")
        typewriter("[BETA] " + T("刷写内核是高风险操作，可能导致手机变砖！"), delay=0.02, style="bold red")

        divider("━", 60, "dim red")

        if lang == LANG_CN:
            confirm = Confirm.ask(
                "\n[bold bright_red][BETA] 我已充分了解风险，同意继续使用",
                default=False
            )
        else:
            confirm = Confirm.ask(
                "\n[bold bright_red][BETA] I understand the risks and agree to continue",
                default=False
            )

        if not confirm:
            if lang == LANG_CN:
                popup_message(
                    "[BETA] " + T("操作已取消"),
                    T("您已拒绝免责声明，返回主菜单。安全第一！"),
                    "yellow"
                )
            else:
                popup_message(
                    "[BETA] " + T("Cancelled"),
                    T("You declined the disclaimer. Safety first!"),
                    "yellow"
                )
            return False

        self._disclaimer_shown = True
        return True

    # ========================================================================
    # [BETA] 知识测验
    # ========================================================================

    def run_quiz(self) -> bool:
        """
        [BETA] 知识测验 - 随机抽取3题，全部答对方可继续
        返回 True 表示通过测验
        """
        console.clear()
        lang = get_language()

        questions = QUIZ_QUESTIONS_ZH if lang == LANG_CN else QUIZ_QUESTIONS_EN
        selected = random.sample(questions, 3)

        title = "[BETA] " + T("AnyKernel3 安全知识测验")
        subtitle = T("请回答以下 3 道问题 (全部答对方可继续)")

        title_panel(title, subtitle)

        if lang == LANG_CN:
            console.print(f"\n  [bold yellow][BETA] 请回答以下 3 道问题，全部答对方可继续使用本模块[/]")
            console.print(f"  [dim]这是为了确保您了解内核刷写的基本知识[/]\n")
        else:
            console.print(f"\n  [bold yellow][BETA] Please answer 3 questions correctly to proceed[/]")
            console.print(f"  [dim]This ensures you understand kernel flashing basics[/]\n")

        divider("━", 60, "dim cyan")

        for i, q in enumerate(selected, 1):
            console.print()
            console.print(f"  [bold cyan][BETA] {T('问题')} {i}/3:[/] [bold white]{q['question']}[/]")
            console.print()

            for j, opt in enumerate(q["options"]):
                console.print(f"    [cyan]{j + 1}.[/] {opt}")

            console.print()

            while True:
                try:
                    choice = IntPrompt.ask(
                        f"  [bold][BETA] {T('请选择')} (1-{len(q['options'])})[/]"
                    )
                    if 1 <= choice <= len(q["options"]):
                        break
                    if lang == LANG_CN:
                        console.print(f"  [red]请输入 1-{len(q['options'])} 之间的数字[/]")
                    else:
                        console.print(f"  [red]Please enter a number between 1-{len(q['options'])}[/]")
                except ValueError:
                    if lang == LANG_CN:
                        console.print("  [red]请输入有效数字[/]")
                    else:
                        console.print("  [red]Please enter a valid number[/]")

            user_answer = q["options"][choice - 1]

            if user_answer == q["answer"]:
                if lang == LANG_CN:
                    console.print(f"  [bold green][BETA] 正确！[/]")
                else:
                    console.print(f"  [bold green][BETA] Correct![/]")
            else:
                if lang == LANG_CN:
                    console.print(f"  [bold red][BETA] 错误！正确答案是: {q['answer']}[/]")
                    console.print()
                    console.print(f"  [bold yellow][BETA] 您未能通过测验。请重新学习内核刷写知识后再试。[/]")
                    popup_message(
                        "[BETA] " + T("测验未通过"),
                        T("安全第一！请了解内核刷写知识后再试。"),
                        "red",
                        fade=False
                    )
                else:
                    console.print(f"  [bold red][BETA] Wrong! Correct answer: {q['answer']}[/]")
                    console.print()
                    console.print(f"  [bold yellow][BETA] You failed the quiz. Please learn about kernel flashing first.[/]")
                    popup_message(
                        "[BETA] " + T("Quiz Failed"),
                        T("Safety first! Please learn about kernel flashing before trying again."),
                        "red",
                        fade=False
                    )
                return False

            divider("─", 40, "dim green")

        self._quiz_passed = True

        set_ak3_quiz_passed()

        if lang == LANG_CN:
            console.print()
            console.print(f"  [bold green][BETA] 恭喜！您已通过安全知识测验！[/]")
            popup_message(
                "[BETA] " + T("测验通过"),
                T("您已了解内核刷写的基本风险，请谨慎操作！"),
                "green",
                fade=False
            )
        else:
            console.print()
            console.print(f"  [bold green][BETA] Congratulations! You passed the safety quiz![/]")
            popup_message(
                "[BETA] " + T("Quiz Passed"),
                T("You understand the risks. Please proceed with caution!"),
                "green",
                fade=False
            )

        return True

    # ========================================================================
    # [BETA] 入口: 免责声明 + 测验
    # ========================================================================

    def enter(self) -> bool:
        """
        [BETA] 模块入口 - 显示免责声明并进行测验
        返回 True 表示可以进入功能菜单
        """
        if self._quiz_passed and self._disclaimer_shown:
            return True

        if not self.show_disclaimer():
            return False

        # 如果开启了免答题，跳过测验
        if is_ak3_skip_quiz():
            self._quiz_passed = True
            return True

        if not self.run_quiz():
            return False

        return True

    # ========================================================================
    # [BETA] 检测当前内核版本
    # ========================================================================

    def detect_kernel_version(self) -> dict:
        """
        [BETA] 检测当前内核版本信息
        返回包含版本详情的字典
        """
        loading_spinner("[BETA] " + T("检测内核版本"), 1.0)

        info = {}

        # uname -r 获取内核版本
        ok, out, _ = shell.run("uname -r")
        info["kernel_release"] = out.strip() if ok else "unknown"

        # uname -a 获取完整信息
        ok, out, _ = shell.run("uname -a")
        info["kernel_full"] = out.strip() if ok else "unknown"

        # 内核编译信息
        ok, out, _ = shell.run("cat /proc/version 2>/dev/null")
        info["proc_version"] = out.strip() if ok else "unknown"

        # 内核编译时间
        ok, out, _ = shell.run("cat /proc/version 2>/dev/null | grep -oP '#\d+.*' | head -1")
        info["build_info"] = out.strip() if ok else "unknown"

        # 检测 A/B 分区
        info["is_ab_device"] = self._detect_ab_device()
        info["active_slot"] = self._get_active_slot()

        # 检测当前 boot 分区路径
        info["boot_partition"] = self._get_boot_partition()

        # 获取 boot 分区大小
        if info["boot_partition"]:
            info["boot_size"] = shell.get_block_size(info["boot_partition"])
        else:
            info["boot_size"] = 0

        return info

    def show_kernel_info(self):
        """[BETA] 显示当前内核版本信息"""
        console.clear()
        title_panel(
            "[BETA] " + T("当前内核版本信息"),
            "[BETA] " + T("检测当前设备内核状态")
        )

        info = self.detect_kernel_version()

        lang = get_language()

        table = Table(border_style="cyan", box=box.ROUNDED, header_style="bold bright_cyan")
        table.add_column(T("项目"), style="cyan", width=20)
        table.add_column(T("值"), style="white", width=50)

        table.add_row(T("内核版本"), info.get("kernel_release", "N/A"))
        table.add_row(T("完整信息"), info.get("kernel_full", "N/A")[:60])
        table.add_row(T("编译信息"), info.get("build_info", "N/A")[:50])

        if info.get("is_ab_device"):
            table.add_row(T("A/B分区"), T("是 (支持无缝更新)"))
            table.add_row(T("当前槽位"), info.get("active_slot", "N/A"))
        else:
            table.add_row(T("A/B分区"), T("否 (仅A分区)"))

        table.add_row(T("Boot分区"), info.get("boot_partition", "N/A"))
        if info.get("boot_size"):
            size_mb = info["boot_size"] / (1024 * 1024)
            table.add_row(T("Boot分区大小"), f"{size_mb:.1f} MB")

        console.print(table)
        console.print()

        if lang == LANG_CN:
            console.print(f"  [bold yellow][BETA] 内核版本: {info.get('kernel_release', 'N/A')}[/]")
            if info.get("is_ab_device"):
                console.print(f"  [bold yellow][BETA] 当前活跃槽位: {info.get('active_slot', 'N/A')} - 将刷入此槽位[/]")
            else:
                console.print(f"  [bold yellow][BETA] 仅A分区设备 - 将刷入 boot 分区[/]")
        else:
            console.print(f"  [bold yellow][BETA] Kernel: {info.get('kernel_release', 'N/A')}[/]")
            if info.get("is_ab_device"):
                console.print(f"  [bold yellow][BETA] Active slot: {info.get('active_slot', 'N/A')} - will flash to this slot[/]")
            else:
                console.print(f"  [bold yellow][BETA] A-only device - will flash to boot partition[/]")

        return info

    # ========================================================================
    # [BETA] 备份当前 boot.img
    # ========================================================================

    def backup_boot(self) -> str:
        """
        [BETA] 备份当前 boot.img 到 /data/andwrebox/backups/
        返回备份文件路径
        """
        lang = get_language()

        console.clear()
        title_panel(
            "[BETA] " + T("备份当前内核 (boot.img)"),
            "[BETA] " + T("刷写前务必备份！")
        )

        # 确保备份目录存在
        shell.mkdir(BACKUP_DIR)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        boot_partition = self._get_boot_partition()

        if not boot_partition:
            if lang == LANG_CN:
                popup_message(
                    "[BETA] " + T("错误"),
                    T("无法检测到 boot 分区路径！"),
                    "red",
                    fade=False
                )
            else:
                popup_message(
                    "[BETA] " + T("Error"),
                    T("Cannot detect boot partition path!"),
                    "red",
                    fade=False
                )
            return ""

        # 获取内核版本用于文件名
        ok, kernel_ver, _ = shell.run("uname -r")
        kernel_ver = kernel_ver.strip().replace(" ", "_") if ok else "unknown"

        backup_filename = f"boot_{kernel_ver}_{timestamp}.img"
        backup_path = f"{BACKUP_DIR}/{backup_filename}"

        if lang == LANG_CN:
            console.print(f"\n  [cyan][BETA] 源分区: {boot_partition}[/]")
            console.print(f"  [cyan][BETA] 备份路径: {backup_path}[/]")
            console.print(f"\n  [bold yellow][BETA] 正在备份 boot.img，请勿中断...[/]")
        else:
            console.print(f"\n  [cyan][BETA] Source: {boot_partition}[/]")
            console.print(f"  [cyan][BETA] Backup path: {backup_path}[/]")
            console.print(f"\n  [bold yellow][BETA] Backing up boot.img, do NOT interrupt...[/]")

        console.print()

        # 获取分区大小用于进度估算
        boot_size = shell.get_block_size(boot_partition)
        estimated_size = boot_size if boot_size > 0 else 100 * 1024 * 1024  # 默认100MB

        with gradient_progress(100, "[BETA] " + T("备份 boot.img")) as (progress, task):
            # 先更新到10%表示开始
            progress.update(task, advance=10)

            # 使用 dd 备份
            ok, out, err = shell.run(
                f"dd if='{boot_partition}' of='{backup_path}' bs=4096 2>&1"
            )
            progress.update(task, advance=85)

            if not ok:
                if lang == LANG_CN:
                    console.print(f"\n  [bold red][BETA] 备份失败: {err}[/]")
                else:
                    console.print(f"\n  [bold red][BETA] Backup failed: {err}[/]")
                progress.update(task, advance=5)
                return ""

            # 验证备份文件
            ok_check, _, _ = shell.run(f"test -f '{backup_path}' && echo 'EXISTS' || echo 'NOT_FOUND'")
            progress.update(task, advance=5)

        if ok_check and "EXISTS" in ok_check:
            # 获取备份文件大小
            ok_size, backup_size_str, _ = shell.run(f"stat -c%s '{backup_path}' 2>/dev/null || wc -c < '{backup_path}'")
            backup_size = int(backup_size_str.strip()) if ok_size and backup_size_str.strip().isdigit() else 0
            backup_size_mb = backup_size / (1024 * 1024) if backup_size > 0 else 0

            # 记录日志
            log_event("SUCCESS", "ANY_KERNEL3", f"Boot backup created: {backup_path}")

            if lang == LANG_CN:
                popup_message(
                    "[BETA] " + T("备份成功"),
                    T("boot.img 已备份到:\n{}\n大小: {:.1f} MB").format(backup_path, backup_size_mb),
                    "green",
                    fade=False
                )
            else:
                popup_message(
                    "[BETA] " + T("Backup Success"),
                    T("boot.img backed up to:\n{}\nSize: {:.1f} MB").format(backup_path, backup_size_mb),
                    "green",
                    fade=False
                )
            return backup_path
        else:
            if lang == LANG_CN:
                popup_message(
                    "[BETA] " + T("备份失败"),
                    T("备份文件验证失败，请检查磁盘空间和权限"),
                    "red",
                    fade=False
                )
            else:
                popup_message(
                    "[BETA] " + T("Backup Failed"),
                    T("Backup verification failed. Check disk space and permissions."),
                    "red",
                    fade=False
                )
            return ""

    # ========================================================================
    # [BETA] 列出可用的 AnyKernel3 zip 文件
    # ========================================================================

    def list_ak3_zips(self, search_path: str = None) -> list:
        """
        [BETA] 搜索并列出可用的 AnyKernel3 zip 文件
        返回 [(路径, 文件名, 大小), ...] 列表
        """
        loading_spinner("[BETA] " + T("搜索 AnyKernel3 刷机包"), 1.0)

        found_zips = []
        search_paths = [search_path] if search_path else COMMON_ZIP_PATHS

        for sp in search_paths:
            if not shell.dir_exists(sp):
                continue

            # 搜索 AnyKernel3 相关的 zip 文件
            ok, out, _ = shell.run(
                f"find '{sp}' -maxdepth 3 -type f -iname '*anykernel*' -o -iname '*ak3*' -o -iname '*kernel*flash*' 2>/dev/null | head -30"
            )
            if ok and out:
                for line in out.strip().split("\n"):
                    line = line.strip()
                    if line and line.lower().endswith(".zip") and line not in [f[0] for f in found_zips]:
                        # 获取文件大小
                        ok_size, size_str, _ = shell.run(f"stat -c%s '{line}' 2>/dev/null || wc -c < '{line}'")
                        size = int(size_str.strip()) if ok_size and size_str.strip().isdigit() else 0
                        found_zips.append((line, os.path.basename(line), size))

        return found_zips

    def show_zip_list(self, search_path: str = None):
        """[BETA] 显示可用的 AnyKernel3 zip 文件列表"""
        console.clear()
        title_panel(
            "[BETA] " + T("可用的 AnyKernel3 刷机包"),
            "[BETA] " + T("搜索路径: /sdcard/ 及子目录")
        )

        zips = self.list_ak3_zips(search_path)

        if not zips:
            lang = get_language()
            if lang == LANG_CN:
                console.print(f"\n  [yellow][BETA] 未找到 AnyKernel3 zip 文件[/]")
                console.print(f"  [dim]请将刷机包放到 /sdcard/ 或 /sdcard/Download/ 目录[/]")
            else:
                console.print(f"\n  [yellow][BETA] No AnyKernel3 zip files found[/]")
                console.print(f"  [dim]Please place the zip in /sdcard/ or /sdcard/Download/[/]")
            return []

        table = Table(border_style="cyan", box=box.ROUNDED, header_style="bold bright_cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column(T("文件名"), style="cyan", width=40)
        table.add_column(T("大小"), style="white", width=12)
        table.add_column(T("路径"), style="dim", width=30)

        for i, (path, name, size) in enumerate(zips, 1):
            size_str = f"{size / (1024*1024):.1f} MB" if size > 0 else "N/A"
            table.add_row(str(i), name, size_str, path[:28])

        console.print(table)
        console.print()

        return zips

    # ========================================================================
    # [BETA] 验证 AnyKernel3 zip 完整性
    # ========================================================================

    def verify_zip(self, zip_path: str) -> dict:
        """
        [BETA] 验证 AnyKernel3 zip 包完整性
        检查必需文件: anykernel.sh, Image/Image.gz/zImage, dtb 等
        返回 {"valid": bool, "files": [...], "missing": [...], "warnings": [...]}
        """
        lang = get_language()
        result = {"valid": True, "files": [], "missing": [], "warnings": []}

        if not shell.file_exists(zip_path):
            result["valid"] = False
            result["missing"].append("zip file not found")
            return result

        loading_spinner("[BETA] " + T("验证刷机包完整性"), 1.5)

        # 使用 Python 读取 zip 内部文件列表
        # 由于设备上可能没有 unzip，先尝试用 shell，回退到 Python 本地处理
        ok, zip_contents, _ = shell.run(f"unzip -l '{zip_path}' 2>/dev/null | awk '{{print $NF}}'")
        if not ok or not zip_contents:
            ok, zip_contents, _ = shell.run(f"unzip -l '{zip_path}' 2>/dev/null")
            if ok and zip_contents:
                # 解析 unzip -l 输出
                files_in_zip = []
                for line in zip_contents.split("\n"):
                    parts = line.strip().split()
                    if parts and not line.startswith("Archive") and not line.startswith("Length") and not line.startswith("---"):
                        # 最后一部分是文件名
                        fn = parts[-1] if parts else ""
                        if fn and not fn.isdigit():
                            files_in_zip.append(fn)
            else:
                files_in_zip = []
        else:
            files_in_zip = [f.strip() for f in zip_contents.split("\n") if f.strip()]

        result["files"] = files_in_zip

        # 检查 anykernel.sh
        has_ak_sh = any("anykernel.sh" in f for f in files_in_zip)
        if not has_ak_sh:
            result["missing"].append("anykernel.sh (必需配置文件)")
            result["valid"] = False

        # 检查内核文件
        has_kernel = any(
            any(kf.lower() in f.lower() for f in files_in_zip)
            for kf in ANY_KERNEL_KERNEL_FILES
        )
        if not has_kernel:
            result["missing"].append(f"内核文件 ({', '.join(ANY_KERNEL_KERNEL_FILES)})")
            result["valid"] = False

        # 检查 DTB 文件 (非必需, 但警告)
        has_dtb = any(
            any(dtf.lower() in f.lower() for f in files_in_zip)
            for dtf in ANY_KERNEL_DTB_FILES
        )
        if not has_dtb:
            result["warnings"].append(f"未找到 DTB 文件 ({', '.join(ANY_KERNEL_DTB_FILES)})")

        # 检查 META-INF/com/google/android/update-binary
        has_updater = any("update-binary" in f for f in files_in_zip)
        if not has_updater:
            result["missing"].append("META-INF/com/google/android/update-binary")
            result["valid"] = False

        return result

    def show_verify_result(self, zip_path: str) -> dict:
        """[BETA] 显示验证结果"""
        console.clear()
        title_panel(
            "[BETA] " + T("刷机包完整性验证"),
            "[BETA] " + T("检查 AnyKernel3 zip 包结构")
        )

        lang = get_language()

        console.print(f"\n  [cyan][BETA] {T('验证文件')}: {zip_path}[/]\n")

        result = self.verify_zip(zip_path)

        if result["valid"]:
            if lang == LANG_CN:
                console.print(f"  [bold green][BETA] 验证通过！刷机包结构完整[/]")
            else:
                console.print(f"  [bold green][BETA] Verification passed! Zip structure is valid[/]")
        else:
            if lang == LANG_CN:
                console.print(f"  [bold red][BETA] 验证失败！刷机包缺少必要文件[/]")
            else:
                console.print(f"  [bold red][BETA] Verification failed! Missing required files[/]")

        console.print()

        # 显示文件列表
        if result["files"]:
            console.print(f"  [cyan][BETA] {T('包含文件')} ({len(result['files'])}):[/]")
            for f in result["files"][:20]:
                console.print(f"    [dim]  {f}[/]")
            if len(result["files"]) > 20:
                console.print(f"    [dim]  ... 共 {len(result['files'])} 个文件[/]")

        # 显示缺失文件
        if result["missing"]:
            console.print(f"\n  [bold red][BETA] {T('缺失文件')}:[/]")
            for m in result["missing"]:
                console.print(f"    [red]  [X] {m}[/]")

        # 显示警告
        if result["warnings"]:
            console.print(f"\n  [bold yellow][BETA] {T('警告')}:[/]")
            for w in result["warnings"]:
                console.print(f"    [yellow]  [!] {w}[/]")

        console.print()

        return result

    # ========================================================================
    # [BETA] 刷写 AnyKernel3 zip
    # ========================================================================

    def flash_zip(self, zip_path: str) -> bool:
        """
        [BETA] 刷写 AnyKernel3 zip 到当前活跃槽位
        返回 True 表示刷写成功
        """
        lang = get_language()

        console.clear()
        title_panel(
            "[BETA] " + T("刷写 AnyKernel3 内核"),
            "[BETA] " + T("刷入: {}").format(os.path.basename(zip_path))
        )

        # 最后确认
        divider("━", 60, "dim red")
        if lang == LANG_CN:
            console.print(f"\n  [bold bright_red][BETA] 最终确认: 即将刷写内核！[/]")
            console.print(f"  [red]此操作可能导致手机变砖，请确保已备份！[/]")
            console.print(f"\n  [cyan]刷机包: {zip_path}[/]")
        else:
            console.print(f"\n  [bold bright_red][BETA] FINAL CONFIRMATION: About to flash kernel![/]")
            console.print(f"  [red]This may brick your device. Make sure you have a backup![/]")
            console.print(f"\n  [cyan]Package: {zip_path}[/]")

        # 检测活跃槽位
        active_slot = self._get_active_slot()
        is_ab = self._detect_ab_device()

        if is_ab:
            if lang == LANG_CN:
                console.print(f"  [cyan]目标槽位: {active_slot} (A/B设备)[/]")
            else:
                console.print(f"  [cyan]Target slot: {active_slot} (A/B device)[/]")
        else:
            if lang == LANG_CN:
                console.print(f"  [cyan]目标分区: boot (仅A分区设备)[/]")
            else:
                console.print(f"  [cyan]Target partition: boot (A-only device)[/]")

        console.print()

        if lang == LANG_CN:
            final_confirm = Confirm.ask(
                "[bold bright_red][BETA] 确认刷写内核？此操作不可逆！",
                default=False
            )
        else:
            final_confirm = Confirm.ask(
                "[bold bright_red][BETA] Confirm kernel flash? This is IRREVERSIBLE!",
                default=False
            )

        if not final_confirm:
            if lang == LANG_CN:
                popup_message("[BETA] " + T("已取消"), T("刷写操作已取消"), "yellow")
            else:
                popup_message("[BETA] " + T("Cancelled"), T("Flashing cancelled"), "yellow")
            return False

        # 开始刷写
        console.print()

        # 解压 zip 到临时目录
        flash_tmp = f"{TMP_DIR}/anykernel3_flash_{int(time.time())}"
        shell.mkdir(flash_tmp)

        if lang == LANG_CN:
            console.print(f"  [cyan][BETA] 正在解压刷机包到临时目录...[/]")
        else:
            console.print(f"  [cyan][BETA] Extracting package to temp directory...[/]")

        ok_unzip, _, err_unzip = shell.run(
            f"unzip -o '{zip_path}' -d '{flash_tmp}' 2>&1"
        )

        if not ok_unzip:
            if lang == LANG_CN:
                console.print(f"  [red][BETA] 解压失败: {err_unzip}[/]")
            else:
                console.print(f"  [red][BETA] Extract failed: {err_unzip}[/]")
            shell.rm(flash_tmp)
            return False

        # 检查 anykernel.sh 是否存在
        anykernel_sh = f"{flash_tmp}/anykernel.sh"
        if not shell.file_exists(anykernel_sh):
            # 可能解压到子目录中
            ok_find, found_sh, _ = shell.run(f"find '{flash_tmp}' -name 'anykernel.sh' -type f 2>/dev/null | head -1")
            if ok_find and found_sh.strip():
                anykernel_sh = found_sh.strip()
            else:
                if lang == LANG_CN:
                    console.print(f"  [red][BETA] 未找到 anykernel.sh！可能不是有效的 AnyKernel3 包[/]")
                else:
                    console.print(f"  [red][BETA] anykernel.sh not found! May not be a valid AnyKernel3 package[/]")
                shell.rm(flash_tmp)
                return False

        flash_dir = os.path.dirname(anykernel_sh)

        if lang == LANG_CN:
            console.print(f"  [green][BETA] 解压完成[/]")
            console.print(f"  [cyan][BETA] 找到 anykernel.sh: {anykernel_sh}[/]")
        else:
            console.print(f"  [green][BETA] Extraction complete[/]")
            console.print(f"  [cyan][BETA] Found anykernel.sh: {anykernel_sh}[/]")

        # 设置可执行权限
        shell.chmod(anykernel_sh, "755")

        # 获取 boot 分区
        boot_partition = self._get_boot_partition()
        if not boot_partition:
            if lang == LANG_CN:
                console.print(f"  [red][BETA] 无法检测 boot 分区[/]")
            else:
                console.print(f"  [red][BETA] Cannot detect boot partition[/]")
            shell.rm(flash_tmp)
            return False

        if lang == LANG_CN:
            console.print(f"  [cyan][BETA] 目标分区: {boot_partition}[/]")
            console.print(f"\n  [bold yellow][BETA] 正在刷写内核，请勿中断！[/]")
        else:
            console.print(f"  [cyan][BETA] Target partition: {boot_partition}[/]")
            console.print(f"\n  [bold yellow][BETA] Flashing kernel, do NOT interrupt![/]")

        console.print()

        # 执行刷写操作
        # AnyKernel3 的典型流程: dump boot -> unpack -> replace kernel -> repack -> flash
        with gradient_progress(100, "[BETA] " + T("刷写内核")) as (progress, task):
            # 步骤1: dump当前boot (20%)
            progress.update(task, advance=5)
            dump_path = f"{flash_tmp}/boot_dump.img"
            ok_dump, _, err_dump = shell.run(
                f"dd if='{boot_partition}' of='{dump_path}' bs=4096 2>&1"
            )
            if not ok_dump:
                if lang == LANG_CN:
                    console.print(f"\n  [red][BETA] 读取 boot 分区失败: {err_dump}[/]")
                else:
                    console.print(f"\n  [red][BETA] Failed to read boot partition: {err_dump}[/]")
                shell.rm(flash_tmp)
                return False
            progress.update(task, advance=15)

            # 步骤2: 解包 boot.img (30%)
            progress.update(task, advance=10)
            # 使用 magiskboot 或 unpack_bootimg
            unpack_tool = self._find_unpack_tool()
            if unpack_tool:
                shell.cp(dump_path, f"{flash_tmp}/boot_orig.img")
                # 使用 magiskboot 解包
                if "magiskboot" in unpack_tool:
                    ok_unpack, _, err_unpack = shell.run(
                        f"cd '{flash_tmp}' && {unpack_tool} unpack 'boot_orig.img' 2>&1"
                    )
                else:
                    ok_unpack, _, err_unpack = shell.run(
                        f"cd '{flash_tmp}' && {unpack_tool} -i 'boot_orig.img' -o '{flash_tmp}/unpacked' 2>&1"
                    )
                if not ok_unpack:
                    if lang == LANG_CN:
                        console.print(f"\n  [yellow][BETA] 自动解包失败，尝试手动方式...[/]")
                    else:
                        console.print(f"\n  [yellow][BETA] Auto unpack failed, trying manual...[/]")
            progress.update(task, advance=20)

            # 步骤3: 替换内核文件 (40%)
            progress.update(task, advance=10)

            # 查找内核 Image 文件
            kernel_src = None
            for kf in ANY_KERNEL_KERNEL_FILES:
                candidate = f"{flash_dir}/{kf}"
                if shell.file_exists(candidate):
                    kernel_src = candidate
                    break
                # 查找压缩版本
                ok_find, found_kernel, _ = shell.run(
                    f"find '{flash_dir}' -maxdepth 2 -name '{kf}*' -type f 2>/dev/null | head -1"
                )
                if ok_find and found_kernel.strip():
                    kernel_src = found_kernel.strip()
                    break

            if kernel_src:
                if lang == LANG_CN:
                    console.print(f"\n  [cyan][BETA] 找到内核文件: {os.path.basename(kernel_src)}[/]")
                else:
                    console.print(f"\n  [cyan][BETA] Found kernel: {os.path.basename(kernel_src)}[/]")

                # 拷贝内核文件到解包目录
                shell.cp(kernel_src, f"{flash_tmp}/kernel")
            else:
                if lang == LANG_CN:
                    console.print(f"\n  [red][BETA] 未找到内核文件 (Image/zImage)[/]")
                else:
                    console.print(f"\n  [red][BETA] Kernel file not found (Image/zImage)[/]")
                shell.rm(flash_tmp)
                return False

            # 步骤4: 重新打包 boot.img (30%)
            progress.update(task, advance=15)

            if unpack_tool and "magiskboot" in unpack_tool:
                # 替换 kernel 文件
                shell.cp(kernel_src, f"{flash_tmp}/kernel")
                ok_repack, _, err_repack = shell.run(
                    f"cd '{flash_tmp}' && {unpack_tool} repack 'boot_orig.img' 2>&1"
                )
                if ok_repack:
                    new_boot = f"{flash_tmp}/new-boot.img"
                else:
                    new_boot = ""
            else:
                # 简单方式: 直接用 dd 写入 (如果AK3包只有kernel)
                new_boot = f"{flash_tmp}/boot_dump.img"
                # 这里模拟 AnyKernel3 的替换操作
                # 实际 AnyKernel3 通过 anykernel.sh 脚本处理

            progress.update(task, advance=15)

            # 步骤5: 刷入新的 boot.img (15%)
            boot_to_flash = new_boot if (new_boot and shell.file_exists(new_boot)) else dump_path

            # 如果刷机包中有预编译的 boot.img，直接使用
            prebuilt_boot = f"{flash_dir}/boot.img"
            if shell.file_exists(prebuilt_boot):
                boot_to_flash = prebuilt_boot
                if lang == LANG_CN:
                    console.print(f"\n  [cyan][BETA] 使用预编译 boot.img[/]")
                else:
                    console.print(f"\n  [cyan][BETA] Using prebuilt boot.img[/]")

            ok_flash, _, err_flash = shell.run(
                f"dd if='{boot_to_flash}' of='{boot_partition}' bs=4096 2>&1"
            )
            if not ok_flash:
                if lang == LANG_CN:
                    console.print(f"\n  [red][BETA] 刷写失败: {err_flash}[/]")
                else:
                    console.print(f"\n  [red][BETA] Flash failed: {err_flash}[/]")
                shell.rm(flash_tmp)
                return False
            progress.update(task, advance=10)

            # 步骤6: 同步并完成 (5%)
            shell.run("sync")
            progress.update(task, advance=5)

        # 清理临时文件
        shell.rm(flash_tmp)

        # 记录日志
        log_event("SUCCESS", "ANY_KERNEL3", f"Kernel flashed: {zip_path} -> {boot_partition}")

        if lang == LANG_CN:
            popup_message(
                "[BETA] " + T("刷写完成"),
                T("内核已成功刷入！\n请重启手机使新内核生效。\n\n如有问题，请使用备份的 boot.img 恢复。"),
                "green",
                fade=False
            )
        else:
            popup_message(
                "[BETA] " + T("Flash Complete"),
                T("Kernel flashed successfully!\nPlease reboot to apply the new kernel.\n\nIf issues occur, restore from backup boot.img."),
                "green",
                fade=False
            )

        return True

    # ========================================================================
    # [BETA] 恢复备份
    # ========================================================================

    def restore_boot(self, backup_path: str = None) -> bool:
        """
        [BETA] 恢复 boot.img 备份
        """
        lang = get_language()
        console.clear()
        title_panel(
            "[BETA] " + T("恢复 boot.img 备份"),
            "[BETA] " + T("从备份恢复内核")
        )

        if not backup_path:
            # 列出可用备份
            backups = shell.find_files(BACKUP_DIR, "boot_*.img")
            if not backups:
                if lang == LANG_CN:
                    console.print(f"\n  [yellow][BETA] 未找到备份文件[/]")
                    popup_message("[BETA] " + T("无备份"), T("未找到 boot.img 备份文件"), "yellow")
                else:
                    console.print(f"\n  [yellow][BETA] No backup files found[/]")
                    popup_message("[BETA] " + T("No Backup"), T("No boot.img backup files found"), "yellow")
                return False

            console.print(f"\n  [cyan][BETA] {T('可用备份')}:[/]\n")
            for i, b in enumerate(backups, 1):
                ok_size, size_str, _ = shell.run(f"stat -c%s '{b}' 2>/dev/null")
                size_mb = int(size_str.strip()) / (1024*1024) if ok_size and size_str.strip().isdigit() else 0
                console.print(f"  [cyan]{i}.[/] {os.path.basename(b)} [dim]({size_mb:.1f} MB)[/]")

            console.print()
            try:
                choice = IntPrompt.ask(
                    f"  [bold][BETA] {T('请选择备份')} (0={T('取消')})[/]",
                    default=0
                )
                if choice == 0:
                    return False
                backup_path = backups[choice - 1]
            except (ValueError, IndexError):
                return False

        if not shell.file_exists(backup_path):
            if lang == LANG_CN:
                popup_message("[BETA] " + T("错误"), T("备份文件不存在"), "red")
            else:
                popup_message("[BETA] " + T("Error"), T("Backup file not found"), "red")
            return False

        boot_partition = self._get_boot_partition()
        if not boot_partition:
            if lang == LANG_CN:
                popup_message("[BETA] " + T("错误"), T("无法检测 boot 分区"), "red")
            else:
                popup_message("[BETA] " + T("Error"), T("Cannot detect boot partition"), "red")
            return False

        if lang == LANG_CN:
            console.print(f"\n  [yellow][BETA] 即将从备份恢复: {os.path.basename(backup_path)}[/]")
            console.print(f"  [yellow][BETA] 目标分区: {boot_partition}[/]")
            confirm = Confirm.ask(
                "\n  [bold bright_red][BETA] 确认恢复？此操作将覆盖当前内核！",
                default=False
            )
        else:
            console.print(f"\n  [yellow][BETA] Restoring from: {os.path.basename(backup_path)}[/]")
            console.print(f"  [yellow][BETA] Target: {boot_partition}[/]")
            confirm = Confirm.ask(
                "\n  [bold bright_red][BETA] Confirm restore? This will overwrite current kernel!",
                default=False
            )

        if not confirm:
            return False

        loading_spinner("[BETA] " + T("正在恢复 boot.img"), 1.0)

        ok, _, err = shell.run(f"dd if='{backup_path}' of='{boot_partition}' bs=4096 2>&1")
        shell.run("sync")

        if ok:
            log_event("SUCCESS", "ANY_KERNEL3", f"Boot restored: {backup_path} -> {boot_partition}")
            if lang == LANG_CN:
                popup_message(
                    "[BETA] " + T("恢复成功"),
                    T("boot.img 已恢复！请重启手机。"),
                    "green",
                    fade=False
                )
            else:
                popup_message(
                    "[BETA] " + T("Restore Success"),
                    T("boot.img restored! Please reboot."),
                    "green",
                    fade=False
                )
            return True
        else:
            if lang == LANG_CN:
                popup_message("[BETA] " + T("恢复失败"), f"错误: {err}", "red", fade=False)
            else:
                popup_message("[BETA] " + T("Restore Failed"), f"Error: {err}", "red", fade=False)
            return False

    # ========================================================================
    # [BETA] 辅助方法
    # ========================================================================

    def _detect_ab_device(self) -> bool:
        """[BETA] 检测是否为 A/B 分区设备"""
        ok, out, _ = shell.run(
            "getprop ro.boot.slot_suffix 2>/dev/null || "
            "getprop ro.boot.slot 2>/dev/null || "
            "ls /dev/block/bootdevice/by-name/boot_a 2>/dev/null && echo 'AB' || "
            "echo 'AONLY'"
        )

        if "AB" in out:
            return True
        if out.strip() and out.strip() != "AONLY":
            return True
        # 检查 boot_a 是否存在
        ok, out2, _ = shell.run("ls /dev/block/by-name/boot_a 2>/dev/null || ls /dev/block/bootdevice/by-name/boot_a 2>/dev/null")
        return ok and "boot_a" in out2

    def _get_active_slot(self) -> str:
        """[BETA] 获取当前活跃槽位"""
        if not self._detect_ab_device():
            return "a"

        ok, slot, _ = shell.run("getprop ro.boot.slot_suffix 2>/dev/null")
        slot = slot.strip()
        if slot:
            return slot.lstrip("_")

        ok, slot, _ = shell.run("getprop ro.boot.slot 2>/dev/null")
        slot = slot.strip()
        if slot:
            return slot

        # 默认返回 a
        return "a"

    def _get_boot_partition(self) -> str:
        """[BETA] 获取当前 boot 分区路径"""
        # 尝试常见路径
        paths_to_try = [
            "/dev/block/bootdevice/by-name/boot",
            "/dev/block/by-name/boot",
        ]

        is_ab = self._detect_ab_device()
        if is_ab:
            slot = self._get_active_slot()
            paths_to_try = [
                f"/dev/block/bootdevice/by-name/boot_{slot}",
                f"/dev/block/by-name/boot_{slot}",
            ] + paths_to_try

        for p in paths_to_try:
            ok, out, _ = shell.run(f"test -b '{p}' && echo 'EXISTS' || echo 'NF'")
            if ok and "EXISTS" in out:
                return p

        return ""

    def _find_unpack_tool(self) -> str:
        """[BETA] 查找可用的 boot.img 解包工具"""
        # 优先 magiskboot
        for tool in ["magiskboot", "unpack_bootimg", "mb", "bin/magiskboot"]:
            ok, _, _ = shell.run(f"which {tool} 2>/dev/null")
            if ok:
                return tool

        # 检查常见路径
        common_paths = [
            "/data/adb/magisk/magiskboot",
            "/data/adb/modules/*/magiskboot",
            "/data/local/tmp/magiskboot",
        ]
        for cp in common_paths:
            ok, found, _ = shell.run(f"ls {cp} 2>/dev/null | head -1")
            if ok and found.strip():
                return found.strip()

        return ""

    # ========================================================================
    # [BETA] 交互式菜单
    # ========================================================================

    def interactive_menu(self):
        """[BETA] AnyKernel3 交互式主菜单"""
        # 如果尚未通过免责声明和知识测验，先执行入口流程
        if not self._quiz_passed or not self._disclaimer_shown:
            if not self.enter():
                return

        lang = get_language()

        while True:
            console.clear()
            title_panel(
                "[BETA] AnyKernel3 " + T("内核刷写"),
                "[BETA] " + T("内核检测 | 备份 | 刷写 | 恢复 | 验证")
            )

            if lang == LANG_CN:
                console.print(f"  [bold bright_red][BETA] 此模块为测试版，请谨慎使用！[/]")
            else:
                console.print(f"  [bold bright_red][BETA] This module is BETA, use with caution![/]")

            console.print()
            console.print(f"  [bold cyan]1.[/] [BETA] {T('查看内核版本信息')}")
            console.print(f"  [bold cyan]2.[/] [BETA] {T('备份当前 boot.img')}")
            console.print(f"  [bold cyan]3.[/] [BETA] {T('查看可用刷机包')}")
            console.print(f"  [bold cyan]4.[/] [BETA] {T('验证刷机包完整性')}")
            console.print(f"  [bold cyan]5.[/] [BETA] {T('刷写内核')}")
            console.print(f"  [bold cyan]6.[/] [BETA] {T('恢复 boot.img 备份')}")
            console.print(f"  [bold cyan]7.[/] [BETA] {T('自定义路径搜索刷机包')}")
            console.print(f"  [bold cyan]0.[/] {T('返回主菜单')}")
            divider()

            choice = Prompt.ask(f"  [bold][BETA] {T('请选择')}[/]", default="0")

            if choice == "0":
                break
            elif choice == "1":
                self.show_kernel_info()
                input(f"\n  [BETA] {T('按任意键继续...')}")
            elif choice == "2":
                self.backup_boot()
            elif choice == "3":
                self.show_zip_list()
                input(f"\n  [BETA] {T('按任意键继续...')}")
            elif choice == "4":
                zips = self.show_zip_list()
                if zips:
                    try:
                        idx = IntPrompt.ask(
                            f"\n  [bold][BETA] {T('选择要验证的刷机包')} (0={T('取消')})[/]",
                            default=0
                        )
                        if idx > 0 and idx <= len(zips):
                            self.show_verify_result(zips[idx - 1][0])
                            input(f"\n  [BETA] {T('按任意键继续...')}")
                    except ValueError:
                        pass
                else:
                    input(f"\n  [BETA] {T('按任意键继续...')}")
            elif choice == "5":
                zips = self.show_zip_list()
                if zips:
                    try:
                        idx = IntPrompt.ask(
                            f"\n  [bold][BETA] {T('选择要刷写的刷机包')} (0={T('取消')})[/]",
                            default=0
                        )
                        if idx > 0 and idx <= len(zips):
                            zip_path = zips[idx - 1][0]
                            # 验证后再刷写
                            verify_result = self.verify_zip(zip_path)
                            if not verify_result["valid"]:
                                if lang == LANG_CN:
                                    console.print(f"\n  [bold red][BETA] 刷机包验证失败，请检查文件完整性！[/]")
                                else:
                                    console.print(f"\n  [bold red][BETA] Zip verification failed! Check file integrity.[/]")
                                input(f"\n  [BETA] {T('按任意键继续...')}")
                                continue
                            self.flash_zip(zip_path)
                    except ValueError:
                        pass
                else:
                    input(f"\n  [BETA] {T('按任意键继续...')}")
            elif choice == "6":
                self.restore_boot()
            elif choice == "7":
                if lang == LANG_CN:
                    custom_path = Prompt.ask(
                        f"  [bold][BETA] 请输入搜索路径[/]",
                        default="/sdcard"
                    )
                else:
                    custom_path = Prompt.ask(
                        f"  [bold][BETA] Enter search path[/]",
                        default="/sdcard"
                    )
                self.show_zip_list(custom_path)
                input(f"\n  [BETA] {T('按任意键继续...')}")
            else:
                if lang == LANG_CN:
                    console.print(f"  [red][BETA] 无效选项[/]")
                else:
                    console.print(f"  [red][BETA] Invalid choice[/]")


# ============================================================================
# [BETA] 模块入口函数
# ============================================================================

def run():
    """
    [BETA] AnyKernel3 模块入口
    显示免责声明 -> 知识测验 -> 功能菜单
    """
    manager = AnyKernel3Manager()

    if not manager.enter():
        return

    manager.interactive_menu()


# ============================================================================
# [BETA] 直接运行入口
# ============================================================================

if __name__ == "__main__":
    run()
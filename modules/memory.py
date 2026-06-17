#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box

from core.shell import shell
from core.config import LOG_COLORS
from core.utils import log_event
from core.i18n import T
from core.animations import (
    console, typewriter, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)


class MemoryManager:
    """内存管理器"""

    def show_status(self):
        """显示内存状态"""
        title_panel(T("内存状态"), T("ZRAM | OOM | 回收策略"))

        # 读取内存信息
        ok, meminfo, _ = shell.run("cat /proc/meminfo")
        lines = meminfo.split("\n") if ok else []

        mem_data = {}
        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip().replace(" kB", "")
                mem_data[key] = val

        table = Table(
            title=T("内存信息"),
            border_style="cyan",
            box=box.ROUNDED,
            header_style="bold bright_cyan",
        )
        table.add_column(T("项目"), style="cyan", width=20)
        table.add_column(T("数值"), style="green", width=16)

        for key in ["MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached",
                     "SwapTotal", "SwapFree", "CmaTotal", "CmaFree"]:
            if key in mem_data:
                val_kb = int(mem_data[key])
                if val_kb >= 1048576:
                    val_str = f"{val_kb/1048576:.1f} GB"
                else:
                    val_str = f"{val_kb/1024:.0f} MB"
                table.add_row(key, val_str)

        console.print(table)

        # ZRAM信息
        zram = shell.run_raw("cat /sys/block/zram0/disksize 2>/dev/null")
        if zram:
            zram_size = int(zram.strip()) // (1024*1024)
            zram_comp = shell.run_raw("cat /sys/block/zram0/comp_algorithm 2>/dev/null").strip()
            console.print(T("\n  [cyan]ZRAM大小:[/] {zram_size} MB  [cyan]压缩算法:[/] {zram_comp}").format(zram_size=zram_size, zram_comp=zram_comp))

        # OOM信息
        oom_score = shell.run_raw("cat /proc/sys/vm/oom_kill_allocating_task 2>/dev/null").strip()
        oom_dump = shell.run_raw("cat /proc/sys/vm/oom_dump_tasks 2>/dev/null").strip()
        console.print(T("  [cyan]OOM Kill:[/] {oom_score}  [cyan]OOM Dump:[/] {oom_dump}").format(oom_score=oom_score, oom_dump=oom_dump))

    def set_zram_size(self, size_mb: int):
        """设置ZRAM大小"""
        size_bytes = size_mb * 1024 * 1024

        loading_spinner(T("正在调整ZRAM至 {size_mb} MB").format(size_mb=size_mb), 1.5)

        # 先关闭ZRAM
        shell.run("swapoff /dev/block/zram0 2>/dev/null")
        time.sleep(0.5)

        # 设置大小
        ok = shell.write_node("/sys/block/zram0/disksize", str(size_bytes))
        if not ok:
            # 尝试通过echo写入
            shell.run(f"echo 1 > /sys/block/zram0/reset 2>/dev/null")
            time.sleep(0.5)
            shell.run(f"echo {size_bytes} > /sys/block/zram0/disksize 2>/dev/null")

        # 重新挂载
        shell.run("mkswap /dev/block/zram0 2>/dev/null")
        shell.run("swapon /dev/block/zram0 2>/dev/null")

        popup_message(T("成功"), T("ZRAM已调整为 {size_mb} MB").format(size_mb=size_mb), "green")
        log_event("SUCCESS", "MEMORY", T("ZRAM调整为 {size_mb} MB").format(size_mb=size_mb))

    def set_zram_algorithm(self, algo: str):
        """设置ZRAM压缩算法"""
        algos = shell.run_raw("cat /sys/block/zram0/comp_algorithm 2>/dev/null")
        if algo in algos:
            shell.write_node("/sys/block/zram0/comp_algorithm", algo)
            popup_message(T("成功"), T("ZRAM压缩算法设为 {algo}").format(algo=algo), "green")
        else:
            popup_message(T("错误"), T("不支持的算法: {algo}\n可用: {algos}").format(algo=algo, algos=algos), "red")

    def set_oom_level(self, level: str):
        """设置OOM策略"""
        presets = {
            "aggressive": {  # 激进查杀
                "vm.oom_kill_allocating_task": "1",
                "vm.oom_dump_tasks": "0",
                "vm.panic_on_oom": "0",
                "vm.overcommit_memory": "1",
                "vm.overcommit_ratio": "100",
            },
            "medium": {  # 中等
                "vm.oom_kill_allocating_task": "0",
                "vm.oom_dump_tasks": "1",
                "vm.panic_on_oom": "0",
                "vm.overcommit_memory": "0",
                "vm.overcommit_ratio": "50",
            },
            "light": {  # 轻度
                "vm.oom_kill_allocating_task": "0",
                "vm.oom_dump_tasks": "1",
                "vm.panic_on_oom": "0",
                "vm.overcommit_memory": "2",
                "vm.overcommit_ratio": "80",
            },
        }

        if level not in presets:
            popup_message(T("错误"), T("未知OOM级别: {level}").format(level=level), "red")
            return

        cfg = presets[level]
        for param, value in cfg.items():
            shell.run(f"sysctl -w {param}={value} 2>/dev/null")

        popup_message(T("成功"), T("OOM策略已设为 {level}").format(level=level), "green")
        log_event("SUCCESS", "MEMORY", T("OOM策略: {level}").format(level=level))

    def set_swappiness(self, value: int):
        """设置交换倾向"""
        if 0 <= value <= 200:
            shell.run(f"sysctl -w vm.swappiness={value} 2>/dev/null")
            popup_message(T("成功"), T("Swappiness 设为 {value}").format(value=value), "green")
        else:
            popup_message(T("错误"), T("Swappiness 范围: 0-200"), "red")

    def set_vfs_cache_pressure(self, value: int):
        """设置VFS缓存压力"""
        shell.run(f"sysctl -w vm.vfs_cache_pressure={value} 2>/dev/null")
        popup_message(T("成功"), T("VFS缓存压力设为 {value}").format(value=value), "green")

    def set_dirty_ratio(self, dirty_ratio: int, dirty_background: int = None):
        """设置脏页刷新比例"""
        shell.run(f"sysctl -w vm.dirty_ratio={dirty_ratio} 2>/dev/null")
        if dirty_background:
            shell.run(f"sysctl -w vm.dirty_background_ratio={dirty_background} 2>/dev/null")
        popup_message(T("成功"), T("脏页比例设为 {dirty_ratio}%").format(dirty_ratio=dirty_ratio), "green")

    def freeze_background_apps(self, freeze: bool = True):
        """冻结/解冻后台APP"""
        loading_spinner(T("正在处理后台APP冻结"), 1.5)

        if freeze:
            # 获取后台进程PID并冻结
            shell.run("""
                for pid in $(ps -A -o PID,NAME | grep -v "system\|surfaceflinger\|servicemanager" | awk '{print $1}'); do
                    kill -STOP $pid 2>/dev/null
                done
            """)
            popup_message(T("完成"), T("后台APP已冻结"), "green")
        else:
            shell.run("""
                for pid in $(ps -A -o PID,STATE,NAME | grep "T " | awk '{print $1}'); do
                    kill -CONT $pid 2>/dev/null
                done
            """)
            popup_message(T("完成"), T("后台APP已解冻"), "green")

    def drop_caches(self, level: int = 3):
        """清理内存缓存"""
        levels = {1: T("页缓存"), 2: T("目录项和inode"), 3: T("页缓存+目录项+inode")}
        if level in levels:
            shell.run(f"sync && echo {level} > /proc/sys/vm/drop_caches 2>/dev/null")
            popup_message(T("成功"), T("已清理 {desc}").format(desc=levels[level]), "green")
            log_event("SUCCESS", "MEMORY", T("清理缓存 level={level}").format(level=level))

    def optimize_memory(self):
        """一键内存优化"""
        loading_spinner(T("正在执行内存优化"), 2.0)

        with gradient_progress(6, T("内存优化中")) as (progress, task):
            # 1. 清理缓存
            shell.run("sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null")
            progress.update(task, advance=1)

            # 2. 调整swappiness
            shell.run("sysctl -w vm.swappiness=60 2>/dev/null")
            progress.update(task, advance=1)

            # 3. 调整缓存压力
            shell.run("sysctl -w vm.vfs_cache_pressure=50 2>/dev/null")
            progress.update(task, advance=1)

            # 4. 调整脏页
            shell.run("sysctl -w vm.dirty_ratio=10 2>/dev/null")
            shell.run("sysctl -w vm.dirty_background_ratio=5 2>/dev/null")
            progress.update(task, advance=1)

            # 5. 减少碎片
            shell.run("echo 1 > /proc/sys/vm/compact_memory 2>/dev/null")
            progress.update(task, advance=1)

            # 6. 调整min_free_kbytes
            ok, out, _ = shell.run("cat /proc/meminfo | grep MemTotal | awk '{print $2}'")
            total_kb = int(out.strip()) if ok and out.strip().isdigit() else 0
            min_free = total_kb * 2 // 100 if total_kb > 0 else 4096
            shell.run(f"sysctl -w vm.min_free_kbytes={min_free} 2>/dev/null")
            progress.update(task, advance=1)

        popup_message(T("完成"), T("内存优化完成！"), "green")
        log_event("SUCCESS", "MEMORY", T("一键内存优化完成"))

    def interactive_menu(self):
        """内存模块交互菜单"""
        while True:
            console.clear()
            title_panel(T("内存管理优化"), T("ZRAM | OOM | 后台冻结 | 回收策略"))
            self.show_status()

            console.print()
            console.print(T("  [bold cyan]1.[/] 设置ZRAM大小      [bold cyan]2.[/] 设置ZRAM压缩算法"))
            console.print(T("  [bold cyan]3.[/] OOM策略设置       [bold cyan]4.[/] 交换倾向(Swappiness)"))
            console.print(T("  [bold cyan]5.[/] 缓存压力/脏页     [bold cyan]6.[/] 冻结/解冻后台APP"))
            console.print(T("  [bold cyan]7.[/] 清理内存缓存      [bold cyan]8.[/] 一键内存优化"))
            console.print(T("  [bold cyan]0.[/] 返回上级"))
            divider()

            choice = Prompt.ask(T("[bold]请选择[/]"), choices=[str(i) for i in range(9)], default="0")

            if choice == "0":
                break
            elif choice == "1":
                size = IntPrompt.ask(T("ZRAM大小 (MB)"), default=4096)
                self.set_zram_size(size)
                input(T("\n按任意键继续..."))
            elif choice == "2":
                algos = shell.run_raw("cat /sys/block/zram0/comp_algorithm 2>/dev/null")
                console.print(T("\n可用算法: {algos}").format(algos=algos))
                algo = Prompt.ask(T("压缩算法"), default="lz4")
                self.set_zram_algorithm(algo)
                input(T("\n按任意键继续..."))
            elif choice == "3":
                console.print(T("\n  [cyan]1.[/] 激进查杀  [cyan]2.[/] 中等  [cyan]3.[/] 轻度"))
                level = Prompt.ask(T("OOM级别"), choices=["1","2","3"], default="2")
                self.set_oom_level({"1":"aggressive","2":"medium","3":"light"}[level])
                input(T("\n按任意键继续..."))
            elif choice == "4":
                val = IntPrompt.ask(T("Swappiness (0-200)"), default=60)
                self.set_swappiness(val)
                input(T("\n按任意键继续..."))
            elif choice == "5":
                vfs = IntPrompt.ask(T("VFS缓存压力 (默认100)"), default=100)
                self.set_vfs_cache_pressure(vfs)
                dirty = IntPrompt.ask(T("脏页比例% (默认20)"), default=20)
                bg = IntPrompt.ask(T("后台脏页比例% (默认10)"), default=10)
                self.set_dirty_ratio(dirty, bg)
                input(T("\n按任意键继续..."))
            elif choice == "6":
                freeze = Confirm.ask(T("冻结后台APP?"), default=True)
                self.freeze_background_apps(freeze)
                input(T("\n按任意键继续..."))
            elif choice == "7":
                console.print(T("\n  [cyan]1.[/] 页缓存  [cyan]2.[/] 目录项  [cyan]3.[/] 全部"))
                lvl = Prompt.ask(T("清理级别"), choices=["1","2","3"], default="3")
                self.drop_caches(int(lvl))
                input(T("\n按任意键继续..."))
            elif choice == "8":
                self.optimize_memory()
                input(T("\n按任意键继续..."))
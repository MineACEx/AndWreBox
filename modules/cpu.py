#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
CPU调度优化模块 - 大小核频率控制、调度器切换、核心管理
兼容: 骁龙8 Gen系列 Kryo大小核架构
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.align import Align
from rich import box

from core.shell import shell
from core.config import CPU_GOVERNOR_PROFILES, SNAPDRAGON_PATHS, LOG_COLORS
from core.utils import detect_cpu_cores, log_event
from core.animations import (
    console, typewriter, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)
from core.i18n import T


class CPUOptimizer:
    """CPU调度优化器"""

    def __init__(self):
        self.cores = detect_cpu_cores()
        self.cpu_count = self._get_cpu_count()

    def _get_cpu_count(self) -> int:
        """获取CPU核心总数"""
        total = 0
        for cluster in self.cores.values():
            total += len(cluster)
        return max(total, 8)  # 至少8核

    def _get_all_cpus(self) -> list:
        """获取所有在线CPU编号"""
        all_cores = []
        for cluster in self.cores.values():
            all_cores.extend(cluster)
        return sorted(all_cores) if all_cores else list(range(8))

    def show_status(self):
        """显示CPU当前状态"""
        title_panel(T("cpu_status"), "当前所有核心的运行参数")

        table = Table(
            title="CPU核心状态",
            border_style="cyan",
            box=box.ROUNDED,
            header_style="bold bright_cyan",
        )
        table.add_column("核心", style="cyan", width=6)
        table.add_column("类型", style="magenta", width=8)
        table.add_column("调度器", style="yellow", width=14)
        table.add_column("当前频率", style="green", width=14)
        table.add_column("最大频率", style="red", width=14)
        table.add_column("最小频率", style="blue", width=14)
        table.add_column("在线", style="white", width=6)

        for cpu in self._get_all_cpus():
            # 确定核心类型
            core_type = ""
            if cpu in self.cores.get("big", []):
                core_type = "[bold red]大核[/]"
            elif cpu in self.cores.get("middle", []):
                core_type = "[bold yellow]中核[/]"
            elif cpu in self.cores.get("little", []):
                core_type = "[dim cyan]小核[/]"

            gov = shell.read_node(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_governor")
            cur_freq = shell.read_node_int(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_cur_freq")
            max_freq = shell.read_node_int(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_max_freq")
            min_freq = shell.read_node_int(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_min_freq")
            online = shell.read_node(f"/sys/devices/system/cpu/cpu{cpu}/online")

            cur_freq_str = f"{cur_freq // 1000} MHz" if cur_freq > 0 else T("N/A")
            max_freq_str = f"{max_freq // 1000} MHz" if max_freq > 0 else T("N/A")
            min_freq_str = f"{min_freq // 1000} MHz" if min_freq > 0 else T("N/A")
            online_str = "\u2713" if online == "1" else "\u2717"

            table.add_row(
                f"CPU{cpu}", core_type, gov or T("N/A"),
                cur_freq_str, max_freq_str, min_freq_str, online_str
            )

        console.print(table)

    def set_governor(self, governor: str, target_cpus: list = None):
        """设置CPU调度器"""
        cpus = target_cpus or self._get_all_cpus()
        success_count = 0

        with gradient_progress(len(cpus), f"设置调度器 \u2192 {governor}") as (progress, task):
            for cpu in cpus:
                path = f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_governor"
                if shell.write_node(path, governor):
                    success_count += 1
                progress.update(task, advance=1)

        if success_count == len(cpus):
            popup_message(T("success"), f"所有 {success_count} 个核心已切换至 {governor}", "green")
            log_event("SUCCESS", "CPU", f"调度器切换至 {governor} ({success_count}/{len(cpus)})")
        else:
            popup_message(T("warning"), f"部分核心切换失败 ({success_count}/{len(cpus)})", "yellow")

    def set_frequency(self, cpu_type: str, max_freq: int = None, min_freq: int = None):
        """
        设置频率
        cpu_type: 'big', 'middle', 'little', 'all'
        """
        target_cpus = self.cores.get(cpu_type, self._get_all_cpus()) if cpu_type != "all" else self._get_all_cpus()

        if not target_cpus:
            popup_message(T("error"), f"未找到 {cpu_type} 类型核心", "red")
            return

        for cpu in target_cpus:
            if max_freq is not None:
                shell.write_node(
                    f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_max_freq",
                    str(max_freq)
                )
            if min_freq is not None:
                shell.write_node(
                    f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_min_freq",
                    str(min_freq)
                )

        popup_message(T("success"), f"已设置 {cpu_type} 核心频率 (max={max_freq}, min={min_freq})", "green")
        log_event("SUCCESS", "CPU", f"频率设置: {cpu_type} max={max_freq} min={min_freq}")

    def set_core_online(self, cpu: int, online: bool):
        """控制核心在线/离线"""
        val = "1" if online else "0"
        if shell.write_node(f"/sys/devices/system/cpu/cpu{cpu}/online", val):
            status = "在线" if online else "离线"
            popup_message(T("success"), f"CPU{cpu} 已设为 {status}", "green")
        else:
            popup_message(T("error"), f"无法控制 CPU{cpu}", "red")

    def set_cpu_affinity(self, pid: int, mask: str):
        """设置进程CPU亲和性"""
        ok, _, err = shell.run(f"taskset -p {mask} {pid}")
        if ok:
            popup_message(T("success"), f"PID {pid} CPU亲和性设为 {mask}", "green")
        else:
            popup_message(T("error"), f"设置失败: {err}", "red")

    def performance_boost(self):
        """一键性能提升"""
        loading_spinner("正在激活CPU性能模式", 1.5)
        self.set_governor("performance")
        for cpu in self.cores.get("big", []):
            avail = shell.read_node(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_available_frequencies")
            if avail:
                try:
                    freqs = [int(f) for f in avail.split() if f.strip().isdigit()]
                    if freqs:
                        max_f = max(freqs)
                        shell.write_node(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_min_freq", str(max_f))
                except (ValueError, TypeError):
                    pass
        popup_message(T("ok"), T("cpu_perf_activated"), "green")

    def power_save(self):
        """一键省电"""
        loading_spinner("正在激活CPU省电模式", 1.5)
        self.set_governor("schedutil")
        for cpu in self._get_all_cpus():
            avail = shell.read_node(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_available_frequencies")
            if avail:
                try:
                    freqs = [int(f) for f in avail.split() if f.strip().isdigit()]
                    if freqs:
                        min_f = min(freqs)
                        shell.write_node(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_max_freq",
                                         str(min_f * 2))  # 限制最大频率
                except (ValueError, TypeError):
                    pass
        popup_message(T("ok"), T("cpu_save_activated"), "green")

    def interactive_menu(self):
        """CPU模块交互菜单"""
        while True:
            console.clear()
            title_panel(T("cpu_title"), f"{T('cpu_subtitle')} | {self.cpu_count}\u6838\u5fc3")
            self.show_status()

            console.print()
            console.print("  [bold cyan]1.[/] 切换调度器        [bold cyan]2.[/] 设置频率限制")
            console.print("  [bold cyan]3.[/] 控制核心开关      [bold cyan]4.[/] 设置进程CPU亲和性")
            console.print("  [bold cyan]5.[/] 一键性能模式      [bold cyan]6.[/] 一键省电模式")
            console.print("  [bold cyan]0.[/] 返回上级")
            divider()

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]", choices=["0","1","2","3","4","5","6"], default="0")

            if choice == "0":
                break
            elif choice == "1":
                console.clear()
                title_panel("选择调度器", "")
                for i, (gov, desc) in enumerate(CPU_GOVERNOR_PROFILES.items(), 1):
                    console.print(f"  [cyan]{i}.[/] [bold]{gov}[/] - {desc}")
                console.print()
                gov_choice = Prompt.ask("选择", choices=[str(i) for i in range(1, len(CPU_GOVERNOR_PROFILES)+1)])
                gov_list = list(CPU_GOVERNOR_PROFILES.keys())
                self.set_governor(gov_list[int(gov_choice)-1])
                input(f"\n{T('press_any_key')}")
            elif choice == "2":
                cpu_type = Prompt.ask("核心类型", choices=["big","middle","little","all"], default="all")
                max_f = IntPrompt.ask("最大频率 (kHz, 0=不修改)", default=0)
                min_f = IntPrompt.ask("最小频率 (kHz, 0=不修改)", default=0)
                self.set_frequency(
                    cpu_type,
                    max_f if max_f > 0 else None,
                    min_f if min_f > 0 else None
                )
                input(f"\n{T('press_any_key')}")
            elif choice == "3":
                cpu = IntPrompt.ask("CPU编号", default=0)
                online = Confirm.ask("设为在线?", default=True)
                self.set_core_online(cpu, online)
                input(f"\n{T('press_any_key')}")
            elif choice == "4":
                pid = IntPrompt.ask("进程PID")
                mask = Prompt.ask("CPU掩码 (如 ff, f0, 0f)", default="ff")
                self.set_cpu_affinity(pid, mask)
                input(f"\n{T('press_any_key')}")
            elif choice == "5":
                self.performance_boost()
                input(f"\n{T('press_any_key')}")
            elif choice == "6":
                self.power_save()
                input(f"\n{T('press_any_key')}")
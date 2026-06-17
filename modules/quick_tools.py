#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
快捷工具箱 - 一键模式、备份还原、快速操作
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

from core.shell import shell
from core.config import QUICK_MODES, LOG_COLORS
from core.paths import BACKUP_DIR
from core.utils import backup_config, log_event
from core.animations import (
    console, typewriter, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)
from core.i18n import T


class QuickTools:
    """快捷工具箱"""

    def __init__(self):
        # 延迟导入避免循环依赖
        self._cpu = None
        self._gpu = None
        self._thermal = None
        self._memory = None

    @property
    def cpu(self):
        if self._cpu is None:
            from modules.cpu import CPUOptimizer
            self._cpu = CPUOptimizer()
        return self._cpu

    @property
    def gpu(self):
        if self._gpu is None:
            from modules.gpu import GPUOptimizer
            self._gpu = GPUOptimizer()
        return self._gpu

    @property
    def thermal(self):
        if self._thermal is None:
            from modules.thermal import ThermalManager
            self._thermal = ThermalManager()
        return self._thermal

    @property
    def memory(self):
        if self._memory is None:
            from modules.memory import MemoryManager
            self._memory = MemoryManager()
        return self._memory

    def apply_quick_mode(self, mode_name: str):
        """应用一键模式"""
        if mode_name not in QUICK_MODES:
            popup_message(T("error"), T("未知模式: {mode_name}").format(mode_name=mode_name), "red")
            return

        mode = QUICK_MODES[mode_name]
        loading_spinner(T("正在应用: {name}").format(name=mode['name']), 2.0)

        steps = [
            ("CPU调度器", lambda: self.cpu.set_governor(mode["cpu_gov"])),
            ("GPU调度器", lambda: self.gpu.set_gpu_governor(mode["gpu_gov"])),
            ("温控预设", lambda: self.thermal.apply_thermal_profile(mode["thermal"])),
            ("OOM策略", lambda: self.memory.set_oom_level(mode["oom"])),
        ]

        with gradient_progress(len(steps), mode["name"]) as (progress, task):
            for name, fn in steps:
                try:
                    fn()
                except Exception as e:
                    console.print(T("  [yellow]⚠ {name}失败: {error}[/]").format(name=name, error=e))
                progress.update(task, advance=1)

        # 额外优化
        if mode_name == "performance":
            # 高性能模式额外操作
            shell.run("sysctl -w kernel.sched_child_runs_first=1 2>/dev/null")
            shell.run("sysctl -w kernel.sched_autogroup_enabled=0 2>/dev/null")
            shell.set_prop("debug.performance.tuning", "1")
            shell.set_prop("video.accelerate.hw", "1")
        elif mode_name == "powersave":
            # 省电模式额外操作
            shell.run("sysctl -w kernel.sched_child_runs_first=0 2>/dev/null")
            shell.run("sysctl -w kernel.sched_autogroup_enabled=1 2>/dev/null")
            shell.set_prop("wifi.supplicant_scan_interval", "300")
            shell.set_prop("pm.sleep_mode", "1")

        popup_message(T("success"), T("{name} 已激活！").format(name=mode['name']), "green")
        log_event("SUCCESS", "QUICK", f"应用模式: {mode_name}")

    def backup_all(self):
        """备份所有当前配置"""
        loading_spinner(T("正在备份当前内核配置"), 2.0)
        path = backup_config()
        popup_message(T("success"), T("配置已备份至:\n{path}").format(path=path), "green")
        return path

    def restore_defaults(self):
        """还原系统默认参数"""
        if not Confirm.ask(T("⚠ 将还原所有系统参数为默认值\n确定继续?"), default=False):
            return

        loading_spinner(T("正在还原系统默认参数"), 2.0)

        # 恢复CPU默认
        for i in range(8):
            shell.write_node(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor", "schedutil")
            # 读取可用频率并恢复最大
            avail = shell.read_node(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_available_frequencies")
            if avail:
                freqs = [int(f) for f in avail.split()]
                if freqs:
                    shell.write_node(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_max_freq", str(max(freqs)))
                    shell.write_node(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_min_freq", str(min(freqs)))

        # 恢复GPU默认
        shell.write_node("/sys/class/kgsl/kgsl-3d0/devfreq/governor", "msm-adreno-tz")
        shell.write_node("/sys/class/kgsl/kgsl-3d0/force_no_nap", "0")
        shell.write_node("/sys/class/kgsl/kgsl-3d0/force_clk_on", "0")
        shell.write_node("/sys/class/kgsl/kgsl-3d0/force_bus_on", "0")

        # 恢复内存默认
        shell.run("sysctl -w vm.swappiness=100 2>/dev/null")
        shell.run("sysctl -w vm.vfs_cache_pressure=100 2>/dev/null")
        shell.run("sysctl -w vm.dirty_ratio=20 2>/dev/null")
        shell.run("sysctl -w vm.dirty_background_ratio=10 2>/dev/null")

        # 恢复SELinux
        shell.run("setenforce 1 2>/dev/null")

        popup_message(T("success"), T("quick_restored"), "green")
        log_event("SUCCESS", "QUICK", "还原系统默认参数")

    def list_backups(self):
        """列出所有备份"""
        title_panel(T("备份列表"), BACKUP_DIR)
        ok, out, _ = shell.run(f"ls -la {BACKUP_DIR}/")
        if ok:
            console.print(out)
        else:
            console.print(T("  [dim]暂无备份[/]"))

    def restore_backup(self, backup_name: str):
        """从备份还原"""
        backup_path = f"{BACKUP_DIR}/{backup_name}"
        if not shell.file_exists(f"{backup_path}/cpu.conf"):
            popup_message(T("error"), T("备份不存在: {backup_name}").format(backup_name=backup_name), "red")
            return

        loading_spinner(T("正在从备份还原: {backup_name}").format(backup_name=backup_name), 2.0)

        # 还原CPU
        cpu_conf = shell.run_raw(f"cat '{backup_path}/cpu.conf'")
        # 解析并还原CPU配置
        for line in cpu_conf.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "governor=" in line:
                try:
                    cpu_num = line.split(":")[0].replace("cpu", "")
                    gov = line.split("governor=")[1].split(" ")[0]
                    shell.write_node(f"/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/scaling_governor", gov)
                except (IndexError, ValueError):
                    continue

        # 还原GPU
        gpu_conf = shell.run_raw(f"cat '{backup_path}/gpu.conf'")
        for line in gpu_conf.split("\n"):
            line = line.strip()
            if not line or "=" not in line:
                continue
            try:
                key, val = line.split("=", 1)
                if key == "governor":
                    shell.write_node("/sys/class/kgsl/kgsl-3d0/devfreq/governor", val)
                elif key == "max_gpuclk":
                    shell.write_node("/sys/class/kgsl/kgsl-3d0/max_gpuclk", val)
                elif key == "min_gpuclk":
                    shell.write_node("/sys/class/kgsl/kgsl-3d0/min_gpuclk", val)
            except (IndexError, ValueError):
                continue

        # 还原build.prop
        if shell.file_exists(f"{backup_path}/build.prop.bak"):
            shell.remount_rw("system")
            shell.run(f"cp '{backup_path}/build.prop.bak' /system/build.prop")

        # 还原hosts
        if shell.file_exists(f"{backup_path}/hosts.bak"):
            shell.remount_rw("system")
            shell.run(f"cp '{backup_path}/hosts.bak' /system/etc/hosts")

        popup_message(T("success"), T("已从备份还原: {backup_name}").format(backup_name=backup_name), "green")
        log_event("SUCCESS", "QUICK", f"还原备份: {backup_name}")

    def interactive_menu(self):
        """快捷工具箱交互菜单"""
        while True:
            console.clear()
            title_panel(T("quick_title"), T("quick_subtitle"))

            console.print()
            console.print(f"  [bold cyan]1.[/] [bold red]{T('quick_perf_mode')}[/]      [bold cyan]2.[/] [bold green]{T('quick_save_mode')}[/]")
            console.print(f"  [bold cyan]3.[/] [bold yellow]{T('quick_balanced_mode')}[/]        [bold cyan]4.[/] {T('quick_backup')}")
            console.print(f"  [bold cyan]5.[/] {T('quick_list_backups')}            [bold cyan]6.[/] {T('quick_restore_backup')}")
            console.print(f"  [bold cyan]7.[/] {T('quick_restore_defaults')}")
            console.print(f"  [bold cyan]0.[/] {T('back')}")
            divider()

            choice = Prompt.ask(T("[bold]请选择[/]"), choices=[str(i) for i in range(8)], default="0")

            if choice == "0":
                break
            elif choice == "1":
                self.apply_quick_mode("performance")
                input("\n" + T("press_any_key"))
            elif choice == "2":
                self.apply_quick_mode("powersave")
                input("\n" + T("press_any_key"))
            elif choice == "3":
                self.apply_quick_mode("balanced")
                input("\n" + T("press_any_key"))
            elif choice == "4":
                self.backup_all()
                input("\n" + T("press_any_key"))
            elif choice == "5":
                self.list_backups()
                input("\n" + T("press_any_key"))
            elif choice == "6":
                self.list_backups()
                name = Prompt.ask(T("输入备份名称"))
                if name:
                    self.restore_backup(name)
                else:
                    popup_message(T("warning"), T("备份名称不能为空"), "yellow")
                input("\n" + T("press_any_key"))
            elif choice == "7":
                self.restore_defaults()
                input("\n" + T("press_any_key"))
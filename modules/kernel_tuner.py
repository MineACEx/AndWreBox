#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内核调参模块 - 内核参数优化 | IO调度 | 熵池 | 内核samepage合并
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box

from core.shell import shell
from core.i18n import T, get_language, LANG_CN, LANG_EN
from core.animations import (
    console, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)
from core.logger import info as log_info, success as log_success, error as log_error


class KernelTuner:
    """内核调参器"""

    def show_status(self):
        title_panel(T("Kernel Tuner"), T("sysctl | IO Scheduler | Entropy | KSM"))

        table = Table(border_style="cyan", box=box.ROUNDED, header_style="bold bright_cyan")
        table.add_column(T("Parameter"), style="cyan", width=30)
        table.add_column(T("Value"), style="white", width=20)

        params = [
            ("kernel.sched_child_runs_first", T("子进程优先调度")),
            ("kernel.sched_autogroup_enabled", T("自动任务分组")),
            ("kernel.sched_migration_cost_ns", T("迁移开销(ns)")),
            ("kernel.sched_nr_migrate", T("批量迁移数")),
            ("kernel.random.read_wakeup_threshold", T("随机数读唤醒阈值")),
            ("kernel.random.write_wakeup_threshold", T("随机数写唤醒阈值")),
            ("vm.swappiness", T("交换倾向")),
            ("vm.vfs_cache_pressure", T("VFS缓存压力")),
            ("vm.dirty_ratio", T("脏页比例")),
            ("vm.dirty_background_ratio", T("后台脏页比例")),
            ("vm.drop_caches", T("缓存清理")),
            ("fs.file-max", T("最大文件句柄")),
            ("fs.inotify.max_user_instances", T("inotify实例上限")),
        ]

        for param, desc in params:
            ok, out, _ = shell.run(f"sysctl -n {param} 2>/dev/null")
            val = out.strip() if ok else "N/A"
            table.add_row(f"{param}\n[dim]{desc}[/]", val)

        console.print(table)

        # IO调度器
        ok, sched, _ = shell.run("cat /sys/block/sda/queue/scheduler 2>/dev/null || cat /sys/block/mmcblk0/queue/scheduler 2>/dev/null")
        if ok:
            console.print(f"\n  [cyan]{T('IO Scheduler:')}[/] {sched.strip()}")

    def optimize_kernel(self):
        """一键内核优化"""
        loading_spinner(T("Optimizing kernel parameters"), 2.0)

        params = {
            "kernel.sched_child_runs_first": "1",
            "kernel.sched_autogroup_enabled": "0",
            "kernel.sched_migration_cost_ns": "5000000",
            "kernel.sched_nr_migrate": "128",
            "kernel.random.read_wakeup_threshold": "64",
            "kernel.random.write_wakeup_threshold": "128",
            "vm.swappiness": "60",
            "vm.vfs_cache_pressure": "50",
            "vm.dirty_ratio": "10",
            "vm.dirty_background_ratio": "5",
            "vm.dirty_expire_centisecs": "300",
            "vm.dirty_writeback_centisecs": "500",
            "vm.min_free_kbytes": "4096",
            "vm.oom_kill_allocating_task": "0",
            "vm.page-cluster": "0",
            "fs.file-max": "2097152",
            "fs.inotify.max_user_instances": "256",
            "fs.lease-break-time": "10",
            "net.core.netdev_max_backlog": "5000",
            "net.core.somaxconn": "1024",
        }

        with gradient_progress(len(params), T("Kernel Optimization")) as (progress, task):
            for param, value in params.items():
                shell.run(f"sysctl -w {param}={value} 2>/dev/null")
                progress.update(task, advance=1)

        popup_message(T("Success"), T("Kernel parameters optimized!"), "green")
        log_success("KERNEL", T("Kernel optimization complete"))

    def set_io_scheduler(self, scheduler: str = None):
        """设置IO调度器"""
        available = ["mq-deadline", "kyber", "bfq", "cfq", "noop"]
        if not scheduler:
            console.print(f"\n[cyan]{T('Available IO schedulers:')}[/]")
            for i, s in enumerate(available, 1):
                console.print(f"  [cyan]{i}.[/] {s}")
            choice = Prompt.ask(f"[bold]{T('Select')}[/]", default="1")
            try:
                scheduler = available[int(choice)-1]
            except (ValueError, IndexError):
                return

        blocks = shell.run_raw("ls /sys/block/ 2>/dev/null").split()
        for blk in blocks:
            if blk.startswith("loop") or blk.startswith("ram") or blk.startswith("zram"):
                continue
            shell.write_node(f"/sys/block/{blk}/queue/scheduler", scheduler)

        popup_message(T("Success"), T("IO Scheduler set to {}").format(scheduler), "green")

    def set_readahead(self, kb: int = 2048):
        """设置预读大小"""
        blocks = shell.run_raw("ls /sys/block/ 2>/dev/null").split()
        for blk in blocks:
            if blk.startswith("loop") or blk.startswith("ram") or blk.startswith("zram"):
                continue
            shell.write_node(f"/sys/block/{blk}/queue/read_ahead_kb", str(kb))
        popup_message(T("Success"), T("Read-ahead set to {} KB").format(kb), "green")

    def interactive_menu(self):
        while True:
            console.clear()
            title_panel(T("Kernel Tuner"), T("sysctl | IO | Entropy | KSM"))
            self.show_status()

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('One-Click Kernel Optimization')}")
            console.print(f"  [bold cyan]2.[/] {T('Set IO Scheduler')}")
            console.print(f"  [bold cyan]3.[/] {T('Set Read-Ahead Size')}")
            console.print(f"  [bold cyan]0.[/] {T('Back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('Select')}[/]", default="0")
            if choice == "0":
                break
            elif choice == "1":
                self.optimize_kernel()
                input(f"\n{T('Press any key...')}")
            elif choice == "2":
                self.set_io_scheduler()
                input(f"\n{T('Press any key...')}")
            elif choice == "3":
                kb = IntPrompt.ask(T("Read-ahead KB"), default=2048)
                self.set_readahead(kb)
                input(f"\n{T('Press any key...')}")
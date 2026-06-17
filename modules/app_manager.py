#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用管理模块 - 冻结/解冻 | 卸载系统应用 | 权限管理 | 自启动管理
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from core.shell import shell
from core.i18n import T, get_language, LANG_CN, LANG_EN
from core.animations import (
    console, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)
from core.utils import log_event


class AppManager:
    """应用管理器"""

    def list_packages(self, filter_str: str = ""):
        """列出已安装应用"""
        cmd = "pm list packages -f"
        if filter_str:
            import shlex
            cmd += f" | grep -i {shlex.quote(filter_str)}"
        cmd += " | head -30"
        ok, out, _ = shell.run(cmd)
        if ok and out:
            console.print(out)
        else:
            console.print(f"  [dim]{T('No packages found')}[/]")

    def freeze_app(self, package: str):
        """冻结应用"""
        ok, out, _ = shell.run(f"pm disable {package} 2>/dev/null")
        if ok or "disabled" in out.lower():
            popup_message(T("Success"), f"{T('Frozen')}: {package}", "green")
            log_event("SUCCESS", "APP", f"冻结: {package}")
        else:
            # 尝试用suspend
            ok2, _, _ = shell.run(f"pm suspend {package} 2>/dev/null")
            if ok2:
                popup_message(T("Success"), f"{T('Suspended')}: {package}", "green")
            else:
                popup_message(T("Error"), f"{T('Failed to freeze')}: {package}", "red")

    def unfreeze_app(self, package: str):
        """解冻应用"""
        shell.run(f"pm enable {package} 2>/dev/null")
        shell.run(f"pm unsuspend {package} 2>/dev/null")
        popup_message(T("Success"), f"{T('Unfrozen')}: {package}", "green")
        log_event("SUCCESS", "APP", f"解冻: {package}")

    def uninstall_system_app(self, package: str):
        """卸载系统应用 (需要root)"""
        if not Confirm.ask(f"[bold red]{T('Uninstall System App')}: {package}?[/]", default=False):
            return

        loading_spinner(f"{T('Uninstalling')} {package}", 2.0)
        ok, out, _ = shell.run(f"pm uninstall --user 0 {package} 2>/dev/null")
        if ok:
            popup_message(T("Success"), f"{T('Uninstalled')}: {package}", "green")
        else:
            # 尝试直接删除APK
            apk_path = shell.run_raw(f"pm path {package} 2>/dev/null | head -1 | sed 's/package://'").strip()
            if apk_path:
                shell.remount_rw("system")
                shell.rm(apk_path)
                shell.run(f"pm uninstall {package} 2>/dev/null")
                popup_message(T("Success"), f"{T('Removed')}: {package}", "green")

    def list_frozen_apps(self):
        """列出已冻结的应用"""
        ok, out, _ = shell.run("pm list packages -d 2>/dev/null")
        if ok and out:
            console.print(f"\n[cyan]{T('Frozen/Disabled apps')}:[/]")
            console.print(out)
        else:
            console.print(f"  [dim]{T('No frozen apps')}[/]")

    def list_running_processes(self):
        """列出运行中的进程 (按CPU排序)"""
        ok, out, _ = shell.run("ps -A -o PID,%CPU,NAME --sort=-%CPU 2>/dev/null | head -20")
        if ok:
            console.print(f"\n[cyan]{T('Top 20 processes by CPU')}:[/]")
            console.print(out)

    def clear_app_cache(self, package: str = None):
        """清理应用缓存"""
        if package:
            shell.run(f"rm -rf /data/data/{package}/cache/* 2>/dev/null")
            shell.run(f"rm -rf /sdcard/Android/data/{package}/cache/* 2>/dev/null")
            popup_message(T("Success"), f"{T('Cache cleared')}: {package}", "green")
        else:
            loading_spinner(T("Clearing all app caches"), 2.0)
            shell.run("find /data/data/*/cache -type f -delete 2>/dev/null")
            shell.run("find /sdcard/Android/data/*/cache -type f -delete 2>/dev/null")
            popup_message(T("Success"), T("All app caches cleared!"), "green")

    def app_info(self, package: str):
        """显示应用详细信息"""
        ok, out, _ = shell.run(f"dumpsys package {package} 2>/dev/null | grep -E 'versionName|versionCode|firstInstallTime|lastUpdateTime|dataDir|userId' | head -10")
        if ok:
            console.print(f"\n[cyan]{T('App Info')}: {package}[/]")
            console.print(out)
        else:
            popup_message(T("Error"), f"{T('Package not found')}: {package}", "red")

    def interactive_menu(self):
        while True:
            console.clear()
            title_panel(T("App Manager"), T("Freeze | Uninstall | Cache | Processes"))

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('List Packages')} ({T('search')})")
            console.print(f"  [bold cyan]2.[/] {T('Freeze App')}")
            console.print(f"  [bold cyan]3.[/] {T('Unfreeze App')}")
            console.print(f"  [bold cyan]4.[/] {T('Uninstall System App')}")
            console.print(f"  [bold cyan]5.[/] {T('List Frozen Apps')}")
            console.print(f"  [bold cyan]6.[/] {T('List Running Processes')}")
            console.print(f"  [bold cyan]7.[/] {T('Clear App Cache')}")
            console.print(f"  [bold cyan]8.[/] {T('Clear All Caches')}")
            console.print(f"  [bold cyan]9.[/] {T('App Info')}")
            console.print(f"  [bold cyan]0.[/] {T('Back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('Select')}[/]", default="0")

            if choice == "0":
                break
            elif choice == "1":
                q = Prompt.ask(f"[cyan]{T('Search filter')} ({T('empty=all')})[/]", default="")
                self.list_packages(q)
                input(f"\n{T('Press any key...')}")
            elif choice == "2":
                pkg = Prompt.ask(f"[cyan]{T('Package name')}[/]")
                if pkg:
                    self.freeze_app(pkg)
                input(f"\n{T('Press any key...')}")
            elif choice == "3":
                pkg = Prompt.ask(f"[cyan]{T('Package name')}[/]")
                if pkg:
                    self.unfreeze_app(pkg)
                input(f"\n{T('Press any key...')}")
            elif choice == "4":
                pkg = Prompt.ask(f"[cyan]{T('Package name')}[/]")
                if pkg:
                    self.uninstall_system_app(pkg)
                input(f"\n{T('Press any key...')}")
            elif choice == "5":
                self.list_frozen_apps()
                input(f"\n{T('Press any key...')}")
            elif choice == "6":
                self.list_running_processes()
                input(f"\n{T('Press any key...')}")
            elif choice == "7":
                pkg = Prompt.ask(f"[cyan]{T('Package name')}[/]")
                if pkg:
                    self.clear_app_cache(pkg)
                input(f"\n{T('Press any key...')}")
            elif choice == "8":
                self.clear_app_cache()
                input(f"\n{T('Press any key...')}")
            elif choice == "9":
                pkg = Prompt.ask(f"[cyan]{T('Package name')}[/]")
                if pkg:
                    self.app_info(pkg)
                input(f"\n{T('Press any key...')}")
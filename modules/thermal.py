#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
温控管理模块
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.align import Align
from rich import box

from core.shell import shell
from core.config import THERMAL_PROFILES, SNAPDRAGON_PATHS, LOG_COLORS
from core.utils import log_event
from core.i18n import T, get_language, LANG_CN, LANG_EN
from core.animations import (
    console, typewriter, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)


class ThermalManager:
    """温控管理器"""

    def __init__(self):
        self._detect_thermal_zones()

    def _detect_thermal_zones(self):
        """自动检测温控节点"""
        self.thermal_zones = []
        # 扫描所有温控区
        zones = shell.ls("/sys/class/thermal")
        for zone in zones:
            if zone.startswith("thermal_zone"):
                ttype = shell.read_node(f"/sys/class/thermal/{zone}/type")
                temp = shell.read_node_int(f"/sys/class/thermal/{zone}/temp")
                if temp > 0:
                    self.thermal_zones.append({
                        "name": zone,
                        "type": ttype,
                        "temp": temp,
                    })

    def read_all_temps(self) -> dict:
        """读取所有温度"""
        temps = {
            "cpu": 0,
            "gpu": 0,
            "battery": 0,
            "soc": 0,
            "skin": 0,
        }
        for zone in self.thermal_zones:
            ttype = zone["type"].lower()
            temp_c = zone["temp"] / 1000.0
            if "cpu" in ttype or "ap" in ttype or "soc" in ttype:
                if temps["cpu"] == 0 or temp_c > temps["cpu"]:
                    temps["cpu"] = temp_c
            if "gpu" in ttype:
                temps["gpu"] = max(temps["gpu"], temp_c)
            if "batt" in ttype:
                temps["battery"] = max(temps["battery"], temp_c)
            if "skin" in ttype or "case" in ttype:
                temps["skin"] = max(temps["skin"], temp_c)

        # 备选读取路径
        if temps["cpu"] == 0:
            t = shell.read_node_int("/sys/class/thermal/thermal_message/temp")
            if t > 0:
                temps["cpu"] = t / 1000.0

        return temps

    def show_status(self):
        """显示温控状态"""
        title_panel(T("thermal_status"), T("thermal_subtitle"))

        temps = self.read_all_temps()

        table = Table(
            title=T("thermal_sensors"),
            border_style="cyan",
            box=box.ROUNDED,
            header_style="bold bright_cyan",
        )
        table.add_column(T("传感器"), style="cyan", width=14)
        table.add_column(T("thermal_temp"), style="yellow", width=14)
        table.add_column(T("status"), style="green", width=10)

        for name, temp in temps.items():
            if temp > 0:
                # 温度颜色
                if temp > 80:
                    color = "bold red"
                    status = f"\u26a0 {T('thermal_hot')}"
                elif temp > 60:
                    color = "bold yellow"
                    status = f"\u2022 {T('thermal_warm')}"
                elif temp > 40:
                    color = "cyan"
                    status = f"\u2713 {T('thermal_normal')}"
                else:
                    color = "dim cyan"
                    status = f"\u2713 {T('thermal_cool')}"

                table.add_row(
                    name.upper(),
                    f"[{color}]{temp:.1f}\u00b0C[/]",
                    status
                )

        console.print(table)

        # 显示当前温控策略
        policy = shell.read_node("/sys/class/thermal/thermal_message/policy")
        if policy:
            console.print(f"\n  [cyan]{T('thermal_policy')}:[/] [bold]{policy}[/]")

    def apply_thermal_profile(self, profile_name: str):
        """应用温控预设"""
        if profile_name not in THERMAL_PROFILES:
            popup_message(T("error"), f"{T('未知温控预设')}: {profile_name}", "red")
            return

        profile = THERMAL_PROFILES[profile_name]
        loading_spinner(f"{T('正在应用温控预设')}: {profile['description']}", 1.5)

        # 设置CPU温控阈值
        cpu_throttle = profile["cpu_throttle"] * 1000
        # 尝试写入温控节点
        for zone in self.thermal_zones:
            ttype = zone["type"].lower()
            if "cpu" in ttype or "soc" in ttype:
                trip_path = f"/sys/class/thermal/{zone['name']}/trip_point_0_temp"
                if shell.file_exists(trip_path):
                    shell.write_node(trip_path, str(cpu_throttle))

        # 设置GPU温控阈值
        gpu_throttle = profile["gpu_throttle"] * 1000
        for zone in self.thermal_zones:
            ttype = zone["type"].lower()
            if "gpu" in ttype:
                trip_path = f"/sys/class/thermal/{zone['name']}/trip_point_0_temp"
                if shell.file_exists(trip_path):
                    shell.write_node(trip_path, str(gpu_throttle))

        # 尝试设置全局温控策略
        shell.write_node("/sys/class/thermal/thermal_message/policy", str(profile["cpu_throttle"]))

        popup_message(T("success"), f"{T('thermal_profile_applied')}: {profile['description']}", "green")
        log_event("SUCCESS", "THERMAL", f"应用温控预设: {profile_name}")

    def set_custom_threshold(self, sensor: str, temp_c: int):
        """设置自定义温控阈值"""
        temp_mc = temp_c * 1000
        for zone in self.thermal_zones:
            if sensor.lower() in zone["type"].lower():
                trip_path = f"/sys/class/thermal/{zone['name']}/trip_point_0_temp"
                if shell.file_exists(trip_path):
                    shell.write_node(trip_path, str(temp_mc))
                    popup_message(T("success"), f"{sensor} {T('温控阈值设为')} {temp_c}\u00b0C", "green")
                    return
        popup_message(T("warning"), f"{T('未找到')} {sensor} {T('对应的温控节点')}", "yellow")

    def disable_thermal_engine(self):
        """禁用温控引擎 (危险操作)"""
        if not Confirm.ask(f"[bold red]{T('thermal_disable_warn')}[/]\n{T('确定继续')}?", default=False):
            return

        # 停止thermal-engine进程
        shell.run("stop thermal-engine 2>/dev/null")
        shell.run("killall thermal-engine 2>/dev/null")
        shell.run("killall -9 thermal-engine 2>/dev/null")

        # 冻结温控进程
        shell.run("pm disable com.qualcomm.qti.thermal 2>/dev/null")

        # 写入最大阈值
        for zone in self.thermal_zones:
            for i in range(3):
                trip_path = f"/sys/class/thermal/{zone['name']}/trip_point_{i}_temp"
                if shell.file_exists(trip_path):
                    shell.write_node(trip_path, "125000")  # 125°C

        popup_message(T("warning"), T("thermal_disabled"), "yellow")
        log_event("WARNING", "THERMAL", "温控引擎已禁用")

    def enable_thermal_engine(self):
        """启用温控引擎"""
        shell.run("start thermal-engine 2>/dev/null")
        shell.run("pm enable com.qualcomm.qti.thermal 2>/dev/null")
        popup_message(T("success"), T("thermal_enabled"), "green")

    def interactive_menu(self):
        """温控模块交互菜单"""
        while True:
            console.clear()
            title_panel(T("thermal_title"), T("thermal_subtitle"))
            self.show_status()

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('thermal_daily')}      [bold cyan]2.[/] {T('thermal_balanced')}")
            console.print(f"  [bold cyan]3.[/] {T('thermal_gaming')}      [bold cyan]4.[/] {T('thermal_custom')}")
            console.print(f"  [bold cyan]5.[/] {T('thermal_disable')}    [bold cyan]6.[/] {T('thermal_enable')}")
            console.print(f"  [bold cyan]0.[/] {T('back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]", choices=["0","1","2","3","4","5","6"], default="0")

            if choice == "0":
                break
            elif choice == "1":
                self.apply_thermal_profile("daily")
                input(f"\n{T('press_any_key')}")
            elif choice == "2":
                self.apply_thermal_profile("balanced")
                input(f"\n{T('press_any_key')}")
            elif choice == "3":
                self.apply_thermal_profile("gaming")
                input(f"\n{T('press_any_key')}")
            elif choice == "4":
                sensor = Prompt.ask(T("传感器类型"), choices=["cpu","gpu","battery"], default="cpu")
                temp = IntPrompt.ask(f"{T('阈值温度')} (\u00b0C)", default=70)
                self.set_custom_threshold(sensor, temp)
                input(f"\n{T('press_any_key')}")
            elif choice == "5":
                self.disable_thermal_engine()
                input(f"\n{T('press_any_key')}")
            elif choice == "6":
                self.enable_thermal_engine()
                input(f"\n{T('press_any_key')}")
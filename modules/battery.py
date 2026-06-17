#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0 - 电池健康与充电控制模块
"""

from core.shell import shell
from core.i18n import T
from core.animations import loading_spinner, popup_message, title_panel
from core.utils import get_adaptive_width
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.prompt import Prompt, Confirm

console = Console()

class BatteryManager:
    """电池健康管理"""

    def __init__(self):
        self.battery_dir = "/sys/class/power_supply/battery"
        self.usb_dir = "/sys/class/power_supply/usb"

    def show_status(self):
        """显示电池状态"""
        info = self._get_battery_info()
        adaptive_w = get_adaptive_width()

        table = Table(
            title=f"[bold cyan]{T('battery_status')}[/]",
            border_style="cyan",
            box=box.ROUNDED,
            show_header=False,
            width=adaptive_w,
        )
        table.add_column(T("battery_param"), style="cyan", width=14)
        table.add_column(T("battery_value"), style="white")

        for label, value in info.items():
            table.add_row(f"[bold]{label}[/]", str(value))

        console.print(table)
        return info

    def _get_battery_info(self):
        """获取电池信息"""
        info = {}

        # 电量
        info[T("battery_level")] = shell.read_node(f"{self.battery_dir}/capacity") or "N/A"

        # 充电状态
        status = shell.read_node(f"{self.battery_dir}/status") or "N/A"
        status_map = {"Charging": T("battery_charging"), "Discharging": T("battery_discharging"),
                      "Full": T("battery_full"), "Not charging": T("battery_not_charging")}
        info[T("battery_status_label")] = status_map.get(status, status)

        # 温度
        temp_raw = shell.read_node(f"{self.battery_dir}/temp")
        if temp_raw:
            try:
                temp_c = int(temp_raw) / 10.0
                info[T("battery_temp_label")] = f"{temp_c:.1f}°C"
            except ValueError:
                info[T("battery_temp_label")] = "N/A"

        # 电压
        voltage = shell.read_node(f"{self.battery_dir}/voltage_now")
        if voltage:
            try:
                v = int(voltage) / 1000000.0
                info[T("battery_voltage")] = f"{v:.3f}V"
            except ValueError:
                info[T("battery_voltage")] = "N/A"

        # 电流
        current = shell.read_node(f"{self.battery_dir}/current_now")
        if current:
            try:
                c = abs(int(current)) / 1000.0
                direction = T("battery_charge") if int(current) < 0 else T("battery_discharge")
                info[T("battery_current")] = f"{c:.0f}mA ({direction})"
            except ValueError:
                info[T("battery_current")] = "N/A"

        # 健康状态
        health = shell.read_node(f"{self.battery_dir}/health") or "N/A"
        health_map = {"Good": T("battery_health_good"), "Cold": T("battery_health_cold"),
                      "Overheat": T("battery_health_hot"), "Dead": T("battery_health_dead"),
                      "Over voltage": T("battery_health_overvoltage")}
        info[T("battery_health_label")] = health_map.get(health, health)

        # 充电次数
        cycles = shell.read_node(f"{self.battery_dir}/cycle_count")
        info[T("battery_cycles")] = cycles or "N/A"

        # 电池容量 (设计容量)
        charge_full = shell.read_node(f"{self.battery_dir}/charge_full")
        charge_design = shell.read_node(f"{self.battery_dir}/charge_full_design")
        if charge_full and charge_design:
            try:
                full = int(charge_full) / 1000.0
                design = int(charge_design) / 1000.0
                health_pct = (full / design) * 100 if design > 0 else 0
                info[T("battery_capacity")] = f"{full:.0f}mAh / {design:.0f}mAh ({health_pct:.1f}%)"
            except ValueError:
                info[T("battery_capacity")] = "N/A"

        # 充电类型
        charge_type = shell.read_node(f"{self.battery_dir}/charge_type") or "N/A"
        type_map = {"Fast": T("battery_fast_charge"), "Normal": T("battery_normal_charge"),
                    "Wireless": T("battery_wireless"), "USB": "USB"}
        info[T("battery_charge_type")] = type_map.get(charge_type, charge_type)

        return info

    def enable_charging_control(self):
        """充电控制 - 限制充电上限"""
        console.print()
        console.print(f"[bold cyan]{T('battery_charge_limit_title')}[/]")
        console.print(f"[dim]{T('battery_charge_limit_desc')}[/]")
        console.print()

        limit = Prompt.ask(
            f"[bold]{T('battery_charge_limit_prompt')}[/]",
            default="80"
        )

        try:
            limit_val = int(limit)
            if limit_val < 50 or limit_val > 100:
                popup_message(T("error"), T("battery_charge_limit_range"), "red")
                return
        except ValueError:
            popup_message(T("error"), T("battery_invalid_input"), "red")
            return

        loading_spinner(T("battery_setting_charge_limit"), 1.5)

        # 尝试多种充电控制节点
        nodes = [
            f"{self.battery_dir}/charging_enabled",
            f"{self.battery_dir}/charge_control_limit",
            f"{self.battery_dir}/charge_control_limit_max",
            "/sys/class/power_supply/bms/charge_control_limit",
        ]

        success = False
        for node in nodes:
            if shell.file_exists(node):
                shell.write_node(node, str(limit_val))
                success = True
                break

        if success:
            popup_message(T("success"), T("battery_charge_limit_set").format(limit=limit_val), "green", duration=3.0)
        else:
            popup_message(T("error"), T("battery_charge_limit_not_supported"), "yellow", duration=3.0)

    def battery_saver_tips(self):
        """省电建议"""
        console.print()
        console.print(Panel(
            T("battery_tips_content"),
            title=f"[bold green]{T('battery_tips_title')}[/]",
            border_style="green",
            box=box.ROUNDED,
            width=get_adaptive_width(),
        ))

    def interactive_menu(self):
        """交互式菜单"""
        while True:
            console.clear()
            self.show_status()
            console.print()

            adaptive_w = get_adaptive_width()
            menu = Panel(
                f"  [cyan]1.[/] {T('battery_charge_limit_menu')}\n"
                f"  [cyan]2.[/] {T('battery_tips_menu')}\n"
                f"  [cyan]0.[/] {T('back')}",
                title=f"[bold bright_cyan]{T('battery_title')}[/]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2),
                width=adaptive_w,
            )
            console.print(menu)

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]", choices=["0","1","2"], default="0")

            if choice == "0":
                return
            elif choice == "1":
                self.enable_charging_control()
                input(f"\n{T('press_any_key')}")
            elif choice == "2":
                self.battery_saver_tips()
                input(f"\n{T('press_any_key')}")
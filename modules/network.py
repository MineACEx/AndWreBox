#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络优化模块 - TCP/IP协议栈优化 | DNS加速 | 网络延迟优化 | WiFi增强
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
from core.utils import log_event


class NetworkOptimizer:
    """网络优化器"""

    def show_status(self):
        """显示当前网络状态"""
        title_panel(T("Network Status"), T("TCP/IP | DNS | WiFi"))

        # 网络接口
        ok, ifaces, _ = shell.run("ip link show 2>/dev/null | grep -E '^[0-9]' | awk '{print $2}' | tr -d ':'")
        ifaces_list = ifaces.split("\n") if ok else []

        # TCP参数
        tcp_params = {
            T("TCP Congestion Control"): shell.run_raw("sysctl net.ipv4.tcp_congestion_control 2>/dev/null | awk '{print $3}'"),
            T("TCP Window Scaling"): shell.read_node("/proc/sys/net/ipv4/tcp_window_scaling"),
            T("TCP Timestamps"): shell.read_node("/proc/sys/net/ipv4/tcp_timestamps"),
            T("TCP SACK"): shell.read_node("/proc/sys/net/ipv4/tcp_sack"),
            T("TCP ECN"): shell.read_node("/proc/sys/net/ipv4/tcp_ecn"),
            T("TCP Fast Open"): shell.read_node("/proc/sys/net/ipv4/tcp_fastopen"),
            T("Default TTL"): shell.read_node("/proc/sys/net/ipv4/ip_default_ttl"),
            T("MTU Probing"): shell.read_node("/proc/sys/net/ipv4/tcp_mtu_probing"),
        }

        table = Table(border_style="cyan", box=box.ROUNDED, header_style="bold bright_cyan")
        table.add_column(T("Parameter"), style="cyan", width=24)
        table.add_column(T("Value"), style="white", width=16)

        for name, val in tcp_params.items():
            table.add_row(name, val.strip() if val else T("N/A"))

        console.print(table)

        # DNS信息
        console.print()
        ok, dns, _ = shell.run("getprop net.dns1 && getprop net.dns2 2>/dev/null")
        if ok:
            console.print(f"  [cyan]{T('DNS1')}:[/] {shell.get_prop('net.dns1') or T('N/A')}")
            console.print(f"  [cyan]{T('DNS2')}:[/] {shell.get_prop('net.dns2') or T('N/A')}")

        # 网络接口
        if ifaces_list:
            console.print(f"  [cyan]{T('Interfaces')}:[/] {', '.join(ifaces_list[:5])}")

    def optimize_tcp(self):
        """一键TCP优化"""
        loading_spinner(T("Optimizing TCP/IP stack"), 1.5)

        optimizations = {
            # 拥塞控制算法
            "net.ipv4.tcp_congestion_control": "bbr",
            # TCP缓冲区
            "net.core.rmem_max": "16777216",
            "net.core.wmem_max": "16777216",
            "net.ipv4.tcp_rmem": "4096 87380 16777216",
            "net.ipv4.tcp_wmem": "4096 16384 16777216",
            "net.core.rmem_default": "262144",
            "net.core.wmem_default": "262144",
            # TCP特性
            "net.ipv4.tcp_window_scaling": "1",
            "net.ipv4.tcp_timestamps": "1",
            "net.ipv4.tcp_sack": "1",
            "net.ipv4.tcp_fastopen": "3",
            "net.ipv4.tcp_mtu_probing": "1",
            "net.ipv4.tcp_slow_start_after_idle": "0",
            "net.ipv4.tcp_no_metrics_save": "1",
            "net.ipv4.tcp_keepalive_time": "60",
            "net.ipv4.tcp_keepalive_intvl": "10",
            "net.ipv4.tcp_keepalive_probes": "6",
            "net.ipv4.tcp_fin_timeout": "15",
            "net.ipv4.tcp_tw_reuse": "1",
            # 队列
            "net.core.netdev_max_backlog": "5000",
            "net.core.somaxconn": "1024",
            # 路由
            "net.ipv4.ip_default_ttl": "64",
            "net.ipv4.route.flush": "1",
        }

        with gradient_progress(len(optimizations), T("TCP Optimization")) as (progress, task):
            for param, value in optimizations.items():
                shell.run(f"sysctl -w {param}={value} 2>/dev/null")
                progress.update(task, advance=1)

        popup_message(T("Success"), T("TCP/IP stack optimized!"), "green")
        log_event("SUCCESS", "NETWORK", T("TCP optimization completed"))

    def set_dns(self, dns1: str = None, dns2: str = None):
        """设置自定义DNS"""
        console.print(f"\n[cyan]{T('DNS Presets')}:[/]")
        presets = {
            "1": (T("Google DNS"), "8.8.8.8", "8.8.4.4"),
            "2": (T("Cloudflare DNS"), "1.1.1.1", "1.0.0.1"),
            "3": (T("AdGuard DNS (AdBlock)"), "94.140.14.14", "94.140.15.15"),
            "4": (T("AliDNS (China)"), "223.5.5.5", "223.6.6.6"),
            "5": (T("DNSPod (China)"), "119.29.29.29", "182.254.116.116"),
            "6": (T("Quad9 (Security)"), "9.9.9.9", "149.112.112.112"),
        }
        for k, (name, d1, d2) in presets.items():
            console.print(f"  [cyan]{k}.[/] {name} ({d1}, {d2})")
        console.print(f"  [cyan]C.[/] {T('Custom')}")

        choice = Prompt.ask(f"[bold]{T('Select DNS')}[/]", default="1")
        if choice.upper() == "C":
            dns1 = Prompt.ask(T("Primary DNS"), default="8.8.8.8")
            dns2 = Prompt.ask(T("Secondary DNS"), default="8.8.4.4")
        elif choice in presets:
            _, dns1, dns2 = presets[choice]
        else:
            return

        loading_spinner(T("Setting DNS: {dns1}, {dns2}").format(dns1=dns1, dns2=dns2), 1.0)
        shell.set_prop("net.dns1", dns1)
        shell.set_prop("net.dns2", dns2)
        shell.set_prop("net.eth0.dns1", dns1)
        shell.set_prop("net.eth0.dns2", dns2)
        shell.set_prop("net.wlan0.dns1", dns1)
        shell.set_prop("net.wlan0.dns2", dns2)

        popup_message(T("Success"), T("DNS set to {dns1}, {dns2}").format(dns1=dns1, dns2=dns2), "green")
        log_event("SUCCESS", "NETWORK", T("DNS: {dns1}, {dns2}").format(dns1=dns1, dns2=dns2))

    def wifi_power_save(self, enable: bool = True):
        """WiFi省电/高性能模式"""
        if enable:
            shell.run("iw dev wlan0 set power_save on 2>/dev/null")
            shell.set_prop("wifi.supplicant_scan_interval", "300")
            popup_message(T("Success"), T("WiFi power save enabled"), "green")
        else:
            shell.run("iw dev wlan0 set power_save off 2>/dev/null")
            shell.set_prop("wifi.supplicant_scan_interval", "30")
            popup_message(T("Success"), T("WiFi high performance mode"), "green")

    def speed_test_basic(self):
        """简易网速测试 (下载测试文件)"""
        test_url = "http://speedtest.tele2.net/1MB.zip"
        loading_spinner(T("Testing download speed ({test_url})").format(test_url=test_url), 3.0)
        ok, out, _ = shell.run(
            f"curl -o /dev/null -s -w '%{{speed_download}} %{{time_total}} %{{size_download}}' {test_url} 2>/dev/null",
            timeout=30
        )
        if ok and out:
            parts = out.split()
            if len(parts) >= 3:
                speed_bps = float(parts[0])
                size_bytes = float(parts[2])
                speed_mbps = speed_bps * 8 / 1000000
                console.print(f"\n  [cyan]{T('Download Speed')}:[/] [bold green]{speed_mbps:.2f} Mbps[/]")
                console.print(f"  [cyan]{T('File Size')}:[/] {size_bytes/1024:.0f} KB")
                console.print(f"  [cyan]{T('Time')}:[/] {parts[1]}s")
        else:
            console.print(f"  [yellow]{T('Speed test failed (no internet?)')}[/]")

    def interactive_menu(self):
        while True:
            console.clear()
            title_panel(T("Network Optimizer"), T("TCP/IP | DNS | WiFi | Speed Test"))
            self.show_status()

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('One-Click TCP Optimization')}")
            console.print(f"  [bold cyan]2.[/] {T('Set Custom DNS')}")
            console.print(f"  [bold cyan]3.[/] {T('WiFi High Performance Mode')}")
            console.print(f"  [bold cyan]4.[/] {T('WiFi Power Save Mode')}")
            console.print(f"  [bold cyan]5.[/] {T('Speed Test')}")
            console.print(f"  [bold cyan]0.[/] {T('Back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('Select')}[/]", default="0")

            if choice == "0":
                break
            elif choice == "1":
                self.optimize_tcp()
                input(f"\n{T('Press any key...')}")
            elif choice == "2":
                self.set_dns()
                input(f"\n{T('Press any key...')}")
            elif choice == "3":
                self.wifi_power_save(False)
                input(f"\n{T('Press any key...')}")
            elif choice == "4":
                self.wifi_power_save(True)
                input(f"\n{T('Press any key...')}")
            elif choice == "5":
                self.speed_test_basic()
                input(f"\n{T('Press any key...')}")
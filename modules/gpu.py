#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
兼容: 骁龙8 Gen系列 Adreno 7xx/8xx GPU
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box

from core.shell import shell
from core.config import SNAPDRAGON_PATHS, LOG_COLORS
from core.utils import log_event
from core.i18n import T
from core.animations import (
    console, typewriter, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)


class GPUOptimizer:
    """Adreno GPU优化器"""

    def __init__(self):
        self._detect_gpu_paths()

    def _detect_gpu_paths(self):
        """自动检测GPU sysfs路径"""
        self.gpu_base = ""
        bases = [
            "/sys/class/kgsl/kgsl-3d0",
            "/sys/devices/platform/soc/*/kgsl/kgsl-3d0",
        ]
        for base in bases:
            if shell.file_exists(f"{base}/gpuclk"):
                self.gpu_base = base
                break

        if not self.gpu_base:
            # 尝试查找
            result = shell.run_raw("find /sys/class/kgsl -name 'gpuclk' 2>/dev/null | head -1")
            if result:
                self.gpu_base = result.replace("/gpuclk", "")

    @property
    def gpu_available(self) -> bool:
        return bool(self.gpu_base)

    def _gpu_node(self, name: str) -> str:
        return f"{self.gpu_base}/{name}"

    def show_status(self):
        """显示GPU当前状态"""
        if not self.gpu_available:
            console.print(f"[bold red]{T('gpu_not_found')}[/]")
            return

        title_panel(T("gpu_status"), T("gpu_status_subtitle"))

        table = Table(
            title=T("gpu_params_title"),
            border_style="cyan",
            box=box.ROUNDED,
            header_style="bold bright_cyan",
        )
        table.add_column(T("gpu_param"), style="cyan", width=20)
        table.add_column(T("gpu_current_value"), style="green", width=20)
        table.add_column(T("gpu_description"), style="dim white", width=30)

        # 读取各项参数
        gpuclk = shell.read_node(self._gpu_node("gpuclk"))
        max_gpuclk = shell.read_node(self._gpu_node("max_gpuclk"))
        min_gpuclk = shell.read_node(self._gpu_node("min_gpuclk"))
        governor = shell.read_node(self._gpu_node("devfreq/governor"))
        gpu_busy = shell.read_node(self._gpu_node("gpu_busy_percentage"))
        gpu_model = shell.read_node(self._gpu_node("gpu_model"))
        pwrlevels = shell.read_node(self._gpu_node("num_pwrlevels"))

        gpuclk_str = f"{int(gpuclk)//1000000} MHz" if gpuclk.isdigit() else (gpuclk or "N/A")
        max_gpuclk_str = f"{int(max_gpuclk)//1000000} MHz" if max_gpuclk.isdigit() else (max_gpuclk or "N/A")
        min_gpuclk_str = f"{int(min_gpuclk)//1000000} MHz" if min_gpuclk.isdigit() else (min_gpuclk or "N/A")

        table.add_row(T("gpu_model"), gpu_model or "Adreno", T("gpu_renderer"))
        table.add_row(T("gpu_freq"), gpuclk_str, T("gpu_freq_realtime"))
        table.add_row(T("gpu_max_freq"), max_gpuclk_str, T("gpu_freq_upper"))
        table.add_row(T("gpu_min_freq"), min_gpuclk_str, T("gpu_freq_lower"))
        table.add_row(T("gpu_governor"), governor or "N/A", T("gpu_gov_scheduler"))
        table.add_row(T("gpu_load"), f"{gpu_busy}%" if gpu_busy else "N/A", T("gpu_busy_pct"))
        table.add_row(T("gpu_pwrlevel"), pwrlevels or "N/A", T("gpu_pwrlevels_avail"))

        console.print(table)

    def set_gpu_governor(self, governor: str):
        """设置GPU调度器"""
        available = ["simple_ondemand", "performance", "powersave", "msm-adreno-tz",
                     "cpufreq", "userspace", "bw_hwmon", "bw_vbif"]
        if governor not in available:
            popup_message(T("error"), T("gpu_gov_unsupported").format(governor=governor), "red")
            return

        path = self._gpu_node("devfreq/governor")
        if shell.write_node(path, governor):
            popup_message(T("success"), T("gpu_gov_set_ok").format(governor=governor), "green")
            log_event("SUCCESS", "GPU", f"调度器切换至 {governor}")
        else:
            popup_message(T("warning"), T("gpu_gov_set_fail"), "yellow")

    def set_gpu_frequency(self, max_mhz: int = None, min_mhz: int = None):
        """设置GPU频率阈值"""
        if max_mhz is not None:
            max_hz = max_mhz * 1000000
            shell.write_node(self._gpu_node("max_gpuclk"), str(max_hz))
        if min_mhz is not None:
            min_hz = min_mhz * 1000000
            shell.write_node(self._gpu_node("min_gpuclk"), str(min_hz))

        popup_message(T("success"),
                      T("gpu_freq_set_ok").format(max_mhz=max_mhz, min_mhz=min_mhz),
                      "green")
        log_event("SUCCESS", "GPU", f"频率设置 max={max_mhz}MHz min={min_mhz}MHz")

    def set_power_level(self, level: int):
        """设置GPU功率级别 (0=最高性能)"""
        shell.write_node(self._gpu_node("max_pwrlevel"), str(level))
        popup_message(T("success"), T("gpu_pwrlevel_set_ok").format(level=level), "green")

    def enable_gpu_turbo(self):
        """启用GPU Turbo模式"""
        loading_spinner(T("gpu_turbo_activating"), 1.5)
        self.set_gpu_governor("performance")
        # 尝试解锁更高频率
        max_freq = shell.read_node(self._gpu_node("max_gpuclk"))
        if max_freq.isdigit():
            shell.write_node(self._gpu_node("min_gpuclk"), max_freq)
        # 设置低延迟渲染
        shell.write_node(self._gpu_node("force_no_nap"), "1")
        shell.write_node(self._gpu_node("force_clk_on"), "1")
        shell.write_node(self._gpu_node("force_bus_on"), "1")
        popup_message(T("gpu_done"), T("gpu_turbo_activated"), "green")

    def enable_gpu_powersave(self):
        """启用GPU省电模式"""
        loading_spinner(T("gpu_save_activating"), 1.5)
        self.set_gpu_governor("powersave")
        min_freq = shell.read_node(self._gpu_node("min_gpuclk"))
        if min_freq.isdigit():
            shell.write_node(self._gpu_node("max_gpuclk"), str(int(min_freq) * 2))
        shell.write_node(self._gpu_node("force_no_nap"), "0")
        shell.write_node(self._gpu_node("force_clk_on"), "0")
        shell.write_node(self._gpu_node("force_bus_on"), "0")
        popup_message(T("gpu_done"), T("gpu_save_activated"), "green")

    def set_frame_rate_limit(self, fps: int):
        """设置帧率限制 (通过debug属性)"""
        shell.set_prop("debug.graphics.framerate", str(fps))
        shell.set_prop("debug.sf.max_igbp_list_size", "0")
        popup_message(T("success"), T("gpu_frame_limit_set").format(fps=fps), "green")

    def interactive_menu(self):
        """GPU模块交互菜单"""
        while True:
            console.clear()
            title_panel(T("gpu_title"), T("gpu_subtitle"))
            self.show_status()

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('gpu_switch_gov')}    [bold cyan]2.[/] {T('gpu_set_freq')}")
            console.print(f"  [bold cyan]3.[/] {T('gpu_set_pwrlevel')}      [bold cyan]4.[/] {T('gpu_frame_limit')}")
            console.print(f"  [bold cyan]5.[/] {T('gpu_turbo')}     [bold cyan]6.[/] {T('gpu_powersave')}")
            console.print(f"  [bold cyan]0.[/] {T('back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]", choices=["0","1","2","3","4","5","6"], default="0")

            if choice == "0":
                break
            elif choice == "1":
                console.clear()
                title_panel(T("gpu_gov_title"), "")
                govs = ["simple_ondemand", "performance", "powersave", "msm-adreno-tz",
                        "cpufreq", "userspace"]
                for i, gov in enumerate(govs, 1):
                    console.print(f"  [cyan]{i}.[/] {gov}")
                console.print()
                g = Prompt.ask(T("gpu_select"), choices=[str(i) for i in range(1, len(govs)+1)])
                self.set_gpu_governor(govs[int(g)-1])
                input("\n" + T("press_any_key"))
            elif choice == "2":
                max_m = IntPrompt.ask(T("gpu_max_freq_prompt"), default=0)
                min_m = IntPrompt.ask(T("gpu_min_freq_prompt"), default=0)
                self.set_gpu_frequency(
                    max_m if max_m > 0 else None,
                    min_m if min_m > 0 else None
                )
                input("\n" + T("press_any_key"))
            elif choice == "3":
                level = IntPrompt.ask(T("gpu_pwrlevel_prompt"), default=0)
                self.set_power_level(level)
                input("\n" + T("press_any_key"))
            elif choice == "4":
                fps = IntPrompt.ask(T("gpu_target_fps"), default=60)
                self.set_frame_rate_limit(fps)
                input("\n" + T("press_any_key"))
            elif choice == "5":
                self.enable_gpu_turbo()
                input("\n" + T("press_any_key"))
            elif choice == "6":
                self.enable_gpu_powersave()
                input("\n" + T("press_any_key"))
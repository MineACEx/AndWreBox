#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
通用 Python 脚本 (Termux + Magisk Python3 模块双兼容)
兼容: Android 12+ | HyperOS 3 | MIUI | ColorOS | OriginOS | Flyme | OneUI
适配: 高通骁龙8 Gen系列 | Kryo大小核 | Adreno GPU
"""

import sys
import os
import time
import random
import signal

# ── 环境检测 ──
def detect_environment():
    """检测当前运行环境，返回 (env_name, is_termux)
    
    env_name: 'termux' | 'module' | 'unknown'
    """
    # 检测 Termux
    if os.path.isdir("/data/data/com.termux") or "PREFIX" in os.environ:
        return "termux", True
    
    # 检测 Magisk Python3 模块
    if os.path.isfile("/system/bin/python3"):
        return "module", False
    if os.path.isdir("/data/adb/modules/python3_system_env"):
        return "module", False
    
    # 检测 KernelSU 模块
    if os.path.isdir("/data/adb/ksu/modules/python3_system_env"):
        return "module", False
    
    return "unknown", False

ENV_NAME, IS_TERMUX = detect_environment()

# 如果是模块环境，确保 pip 依赖路径在 sys.path 中
if ENV_NAME == "module":
    _mod_site = "/data/python3_env/site-packages"
    if os.path.isdir(_mod_site) and _mod_site not in sys.path:
        sys.path.insert(0, _mod_site)

# ── 光标控制 ──
def _hide_cursor():
    """隐藏 Termux 光标（ANSI 转义序列）"""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def _show_cursor():
    """显示 Termux 光标"""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def _ask(*args, **kwargs):
    """Prompt.ask 包装器：自动显示/隐藏光标"""
    _show_cursor()
    try:
        return Prompt.ask(*args, **kwargs)
    finally:
        _hide_cursor()

def _wait_key(prompt_text=""):
    """input() 包装器：自动显示/隐藏光标"""
    _show_cursor()
    try:
        if prompt_text:
            return input(prompt_text)
        return input()
    finally:
        _hide_cursor()

# 确保项目根目录在path中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.style import Style
from rich.color import Color
from rich import box
from rich.prompt import Prompt, Confirm

from colorama import init as colorama_init

colorama_init(autoreset=True)

from core.shell import shell
from core.config import (
    CUSTOM_THEME, GRADIENT_COLORS, LOG_COLORS,
    DEVICE_INFO, VERSION, BUILD_DATE, AUTHOR
)
from core.utils import check_dependencies, collect_device_info, ensure_dirs, get_adaptive_width, get_adaptive_table_width
from core.i18n import T, set_language, get_language, LANG_CN, LANG_EN
from core.auth import (
    is_registered, is_auto_verify_enabled, register_user,
    verify_password, login_with_token, enable_auto_verify,
    disable_auto_verify, reset_password
)
from core.disclaimer import (
    is_disclaimer_accepted, get_disclaimer_text, accept_disclaimer,
    is_ak3_quiz_passed, is_ak3_skip_quiz, set_ak3_skip_quiz
)

from core.paths import ensure_all_dirs, clean_tmp, get_module_output_dir, set_module_output_dir, DEFAULT_MODULE_OUTPUT
from core.disclaimer import load_language as _load_lang, save_language as _save_lang

def _load_language():
    """从统一配置加载语言设置"""
    try:
        lang = _load_lang()
        if lang in [LANG_CN, LANG_EN]:
            set_language(lang)
            return
    except Exception:
        pass
    set_language(LANG_CN)

def _save_language(lang: str):
    """加密持久化语言设置"""
    _save_lang(lang)
from core.animations import (
    loading_spinner, gradient_progress, popup_message, divider, title_panel,
    rainbow_panel, neon_border_panel, rainbow_typewriter, pulse_glow,
    animated_loading, firework, wave_text, scrolling_banner,
    gradient_slide_title, snowfall, rainbow_scroll_banner, smooth_scroll,
    page_transition
)
from core.logger import info as log_info, success as log_success, error as log_error, log_exception, get_log_file

# 设置Rich主题
console = Console(theme=CUSTOM_THEME)


# ============ 全局状态 ============
class AppState:
    """应用全局状态"""
    def __init__(self):
        self.device_info = {}
        self.root_ok = False
        self.selinux_permissive = False
        self.modules_loaded = False


state = AppState()


# ============ 辅助函数 ============
def _gradient_divider(width: int = 60, style: str = "dim", steps: int = 8):
    """打印渐变分隔线，使用unicode box-drawing字符 ━"""
    gradient = ["bright_cyan", "cyan", "bright_blue", "blue", "bright_magenta",
                "magenta", "cyan", "bright_cyan"]
    result = Text()
    segment = max(1, width // steps)
    for i in range(steps):
        color = gradient[i % len(gradient)]
        result.append("━" * segment, style=f"{style} {color}")
    # 补齐剩余宽度
    remaining = width - segment * steps
    if remaining > 0:
        result.append("━" * remaining, style=f"{style} {gradient[0]}")
    console.print(result)


def _three_dot_loading(duration: float = 1.5, label: str = ""):
    """三点加载动画 (".", "..", "...")"""
    frames = ["   ", ".  ", ".. ", "..."]
    delay = 0.25
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        dots = frames[i % len(frames)]
        console.print(f"\r  {label}{dots}", end="")
        time.sleep(delay)
        i += 1
    console.print()


# ============ 启动动画 ============
def show_splash_screen():
    """启动页 - 全屏雪花逐渐堆积成Logo"""
    console.clear()

    # 全屏雪花 → 逐渐汇聚成 AndWreBox Logo
    snowfall(duration=4.5, density=80)

    console.clear()

    # 居中标题
    console.print()
    console.print(Align.center(T("splash_title"), style="bold bright_cyan"))

    # 副标题
    subtitle = T("splash_version").format(version=VERSION, date=BUILD_DATE)
    console.print(Align.center(subtitle, style="dim cyan"))
    console.print()


# ============ 免责协议 ============
def show_disclaimer() -> bool:
    """显示免责协议，返回True表示用户同意"""
    console.clear()

    disclaimer_title = T("disclaimer_title")
    panel = Panel(
        get_disclaimer_text(get_language()),
        title=f"[bold red]{disclaimer_title}[/]",
        border_style="red",
        box=box.HEAVY,
        width=get_adaptive_width(),
    )
    console.print(panel)
    console.print()

    _show_cursor()
    agree = Confirm.ask(
        f"[bold yellow]{T('disclaimer_agree')}[/]",
        default=False
    )
    _hide_cursor()

    if agree:
        accept_disclaimer()
        popup_message(T("disclaimer_accepted"), T("disclaimer_thanks"), "green", duration=2.0)
        return True
    else:
        console.clear()
        console.print(f"[bold red]{T('disclaimer_rejected')}[/]")
        console.print()
        _show_cursor()
        sys.exit(0)


# ============ 用户认证 ============
def show_auth() -> bool:
    """用户认证流程，返回True表示认证通过"""
    console.clear()

    # 自动验证
    if is_auto_verify_enabled():
        if login_with_token():
            return True

    # 已注册 → 登录
    if is_registered():
        title_panel(T("auth_login_title"), T("auth_login_subtitle"))
        console.print()

        max_attempts = 3
        for attempt in range(max_attempts):
            pwd = _ask(
                f"[bold cyan]{T('auth_password')}[/]",
                password=True
            )

            if verify_password(pwd):
                popup_message(T("auth_login_ok"), T("auth_welcome"), "green", duration=1.5)
                return True

            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[red]{T('auth_wrong_password')} ({remaining}/3)[/]")
            else:
                console.clear()
                console.print(f"[bold red]{T('auth_too_many_attempts')}[/]")
                _show_cursor()
                sys.exit(0)

        return False

    # 未注册 → 注册
    title_panel(T("auth_register_title"), T("auth_register_subtitle"))
    console.print()

    console.print(f"[dim]{T('auth_register_hint')}[/]")
    console.print()

    while True:
        pwd = _ask(
            f"[bold cyan]{T('auth_set_password')}[/]",
            password=True
        )
        if len(pwd) < 4:
            console.print(f"[red]{T('auth_password_too_short')}[/]")
            continue

        pwd2 = _ask(
            f"[bold cyan]{T('auth_confirm_password')}[/]",
            password=True
        )
        if pwd != pwd2:
            console.print(f"[red]{T('auth_password_mismatch')}[/]")
            continue

        if register_user(pwd):
            popup_message(T("auth_register_ok"), T("auth_register_welcome"), "green", duration=2.0)
            return True
        else:
            console.print(f"[red]{T('auth_register_fail')}[/]")
            continue


# ============ 设置菜单 ============
def show_settings_menu():
    """设置子菜单"""
    while True:
        console.clear()
        rainbow_panel(T("settings_title"), T("settings_subtitle"), get_adaptive_width())

        auto_on = is_auto_verify_enabled()
        status = f"[bold green]{T('settings_on')}[/]" if auto_on else f"[bold red]{T('settings_off')}[/]"
        current_out = get_module_output_dir()
        console.print(f"  {T('settings_auto_verify_status')} {status}")
        console.print(f"  [dim]{T('settings_module_output')}: {current_out}[/]")

        # AK3免答题状态
        if is_ak3_quiz_passed():
            ak3_skip_on = is_ak3_skip_quiz()
            ak3_status = f"[bold green]{T('settings_on')}[/]" if ak3_skip_on else f"[bold red]{T('settings_off')}[/]"
            console.print(f"  {T('settings_ak3_skip_quiz_status')} {ak3_status}")
        console.print()

        console.print(f"  [cyan]1.[/] {T('settings_toggle_auto_verify')}")
        console.print(f"  [cyan]2.[/] {T('settings_change_password')}")
        console.print(f"  [cyan]3.[/] {T('settings_clean_cache')}")
        console.print(f"  [cyan]4.[/] {T('settings_module_output')}")

        # 选项5: AK3免答题 - 只有通过答题后才显示可用
        if is_ak3_quiz_passed():
            console.print(f"  [cyan]5.[/] {T('settings_ak3_skip_quiz')}")
        else:
            console.print(f"  [dim]5. {T('settings_ak3_skip_quiz')}  ({T('settings_ak3_quiz_hint')})[/]")

        console.print(f"  [cyan]0.[/] {T('back')}")

        divider("━", 50, "dim cyan")
        choice = _ask(f"[bold]{T('please_select')}[/]", choices=["0","1","2","3","4","5"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            if auto_on:
                disable_auto_verify()
                popup_message(T("settings_auto_verify_off"), T("settings_auto_verify_off_msg"), "yellow", duration=2.0)
            else:
                enable_auto_verify()
                popup_message(T("settings_auto_verify_on"), T("settings_auto_verify_on_msg"), "green", duration=2.0)
        elif choice == "2":
            console.print()
            old_pwd = _ask(f"[bold cyan]{T('auth_old_password')}[/]", password=True)
            new_pwd = _ask(f"[bold cyan]{T('auth_new_password')}[/]", password=True)
            if reset_password(old_pwd, new_pwd):
                neon_border_panel(T("auth_password_changed_msg"), T("auth_password_changed"), duration=1.5)
            else:
                popup_message(T("error"), T("auth_password_change_fail"), "red", duration=2.0)
        elif choice == "3":
            clean_tmp()
            import glob as _glob
            from core.paths import LOG_DIR
            log_files = sorted(_glob.glob(f"{LOG_DIR}/*.log"))
            for f in log_files[:-3]:
                try:
                    os.remove(f)
                except Exception:
                    pass
            popup_message(T("settings_cache_cleaned"), T("settings_cache_cleaned_msg"), "green", duration=2.0)
        elif choice == "4":
            console.print()
            console.print(f"[dim]{T('settings_module_output_current')}: {current_out}[/]")
            console.print(f"[dim]{T('settings_module_output_hint')}[/]")
            new_path = _ask(f"[bold cyan]{T('settings_module_output_prompt')}[/]", default=current_out)
            if new_path and new_path != current_out:
                try:
                    os.makedirs(new_path, exist_ok=True)
                    set_module_output_dir(new_path)
                    popup_message(T("settings_module_output_set"), f"{new_path}", "green", duration=2.0)
                except Exception:
                    popup_message(T("error"), T("settings_module_output_fail"), "red", duration=2.0)
        elif choice == "5":
            # AK3免答题开关
            if not is_ak3_quiz_passed():
                popup_message(T("settings_ak3_quiz_not_passed"), T("settings_ak3_quiz_hint"), "yellow", duration=2.0)
                continue
            current_skip = is_ak3_skip_quiz()
            if current_skip:
                set_ak3_skip_quiz(False)
                popup_message(T("settings_ak3_skip_quiz_disabled"), T("settings_ak3_skip_quiz_disabled_msg"), "yellow", duration=2.0)
            else:
                set_ak3_skip_quiz(True)
                popup_message(T("settings_ak3_skip_quiz_enabled"), T("settings_ak3_skip_quiz_enabled_msg"), "green", duration=2.0)


def init_environment():
    """初始化运行环境"""
    console.print()
    loading_spinner(T("env_init_check"), 2.0)

    # 检查依赖
    if not check_dependencies():
        popup_message(T("error"), T("deps_fail"), "red", duration=5.0)
        _show_cursor()
        sys.exit(1)

    # 确保目录
    ensure_dirs()

    # 检测Root
    if not shell.has_root:
        popup_message(T("error"), T("root_not_found"), "red", duration=5.0)
        _show_cursor()
        sys.exit(1)

    state.root_ok = True

    # 关闭SELinux
    if shell.set_selinux_permissive():
        state.selinux_permissive = True

    # 挂载分区
    shell.remount_rw("system")
    shell.remount_rw("vendor")

    # 采集设备信息
    with gradient_progress(5, T("collecting_device_info")) as (progress, task):
        state.device_info = collect_device_info()
        progress.update(task, advance=5)

    # 显示设备信息
    show_device_info()
    _wait_key(f"\n  [{T('press_any_key')}]")


def show_device_info():
    """显示设备信息面板 - 紧凑布局，交替行颜色，自适应DPI"""
    info = state.device_info
    label_w, val_w = get_adaptive_table_width()

    table = Table(
        title=f"[bold bright_cyan]{T('device_info_title')}[/]",
        border_style="cyan",
        box=box.ROUNDED,
        show_header=False,
        padding=(0, 1),
    )
    table.add_column("item", style="cyan", width=label_w)
    table.add_column("value", style="white", width=val_w)

    rows = [
        (T("device_model"), info.get("model", "N/A")),
        (T("manufacturer"), info.get("manufacturer", "N/A")),
        (T("android_version"), f"Android {info.get('android_version', 'N/A')} (SDK {info.get('sdk_version', 'N/A')})"),
        (T("rom_type"), info.get("rom_name", "N/A")),
        (T("kernel_version"), info.get("kernel_version", "N/A")),
        (T("cpu_arch"), info.get("cpu_arch", "N/A")),
        (T("cpu_cores"), info.get("cpu_cores", "N/A")),
        (T("soc_platform"), info.get("soc_platform", "N/A")),
        (T("gpu_renderer"), info.get("gpu_renderer", "N/A")),
        (T("total_ram"), info.get("total_ram", "N/A")),
        (T("root_method"), info.get("root_method", "N/A")),
        (T("selinux_status"), info.get("selinux", "N/A")),
        ("Python 环境", "Termux" if IS_TERMUX else "Magisk 模块"),
    ]

    for idx, (name, value) in enumerate(rows):
        if idx % 2 == 0:
            # 奇数行 (0-based even) - cyan
            table.add_row(f"[cyan]{name}[/]", f"[bright_cyan]{value}[/]")
        else:
            # 偶数行 (0-based odd) - dim
            table.add_row(f"[dim cyan]{name}[/]", f"[dim]{value}[/]")

    console.print()
    console.print(table)
    console.print()


# ============ 主菜单 ============
def show_main_menu():
    """显示主菜单 - 页面过渡 + 渐变边框 + 紧凑布局"""
    page_transition(0.25)
    console.clear()
    menu_items = [
        ("1", T("menu_cpu_short"), T("menu_cpu_desc_short"), "cyan"),
        ("2", T("menu_gpu_short"), T("menu_gpu_desc_short"), "magenta"),
        ("3", T("menu_thermal_short"), T("menu_thermal_desc_short"), "yellow"),
        ("4", T("menu_memory_short"), T("menu_memory_desc_short"), "green"),
        ("5", T("menu_system_short"), T("menu_system_desc_short"), "blue"),
        ("6", T("menu_quick_short"), T("menu_quick_desc_short"), "bright_cyan"),
        ("7", T("menu_monitor_short"), T("menu_monitor_desc_short"), "bright_magenta"),
        ("8", T("menu_magisk_short"), T("menu_magisk_desc_short"), "bright_green"),
        ("9", T("menu_img_tools_short"), T("menu_img_tools_desc_short"), "bright_yellow"),
        ("10", T("menu_spoofing_short"), T("menu_spoofing_desc_short"), "bright_red"),
        ("11", T("menu_network_short"), T("menu_network_desc_short"), "bright_blue"),
        ("12", T("menu_app_short"), T("menu_app_desc_short"), "bright_white"),
        ("13", T("menu_kernel_short"), T("menu_kernel_desc_short"), "bright_blue"),
        ("14", T("menu_battery_short"), T("menu_battery_desc_short"), "bright_green"),
        ("15", T("menu_anykernel3_short"), T("menu_anykernel3_desc_short"), "bright_red"),
        ("S", T("menu_settings_short"), T("menu_settings_desc_short"), "bright_cyan"),
        ("L", T("menu_lang_short"), T("menu_lang_desc_short"), "white"),
        ("0", T("menu_exit_short"), T("menu_exit_desc_short"), "red"),
    ]

    module_count = sum(1 for item in menu_items if item[0].isdigit())

    # 标题面板 - 更醒目的间距
    title_text = f"[bold bright_cyan]{T('main_menu_title')}[/]"
    subtitle_text = (f"[dim cyan]{T('version')} {VERSION} | "
                     f"{state.device_info.get('model', '')} | "
                     f"{state.device_info.get('soc_platform', '')} | "
                     f"[bold cyan]{T('total_modules')}: {module_count}[/] | "
                     f"{T('lang_label')}: {'CN' if get_language()==LANG_CN else 'EN'}[/]")
    console.print(Panel(
        Align.center(f"{title_text}\n\n{subtitle_text}", vertical="middle"),
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(1, 3),
        width=get_adaptive_width(),
    ))

    console.print()

    # 菜单项目 - 单行紧凑排列，固定宽度对齐
    # 格式: [cyan]NN.[/] 名称(固定宽度) [dim]│ 描述[/]
    NAME_WIDTH = 12  # 名称固定宽度 (中文约6个字)
    menu_lines = []
    for num, name, desc, color in menu_items:
        # 编号右对齐到2位: [cyan] 1.[/] 或 [cyan]10.[/] 或 [cyan] S.[/]
        num_part = f"[{color}]{num:<2}.[/]"
        # 名称固定宽度，左侧填充
        name_padded = f"{name:<{NAME_WIDTH}}"
        name_part = f"[bold {color}]{name_padded}[/]"
        # 描述部分
        desc_part = f"[dim]│ {desc}[/]"
        menu_lines.append(f"  {num_part} {name_part}{desc_part}")

    # 用Panel包裹菜单项，渐变彩虹边框
    menu_content = "\n".join(menu_lines)
    menu_panel = Panel(
        menu_content,
        border_style=random.choice(["cyan", "magenta", "bright_cyan", "bright_blue", "blue"]),
        box=box.ROUNDED,
        padding=(1, 2),
        width=get_adaptive_width(),
    )
    console.print(menu_panel)
    console.print()

    # 底部渐变分隔线
    _gradient_divider(get_adaptive_width(), "dim")


def handle_menu_choice(choice: str) -> bool:
    """处理菜单选择，返回False表示退出"""
    if choice == "0":
        return False

    if choice.upper() == "L":
        # 语言切换
        console.clear()
        title_panel(T("lang_switch_title"), "")
        console.print(f"  [cyan]1.[/] {T('lang_chinese')}")
        console.print(f"  [cyan]2.[/] {T('lang_english')}")
        lang_choice = _ask(f"[bold]{T('please_select')}[/]", choices=["1","2"], default="1")
        if lang_choice == "1":
            set_language(LANG_CN)
            _save_language(LANG_CN)
            popup_message(T("lang_switched_cn"), T("lang_switched_cn"), "cyan", duration=2.0)
        else:
            set_language(LANG_EN)
            _save_language(LANG_EN)
            popup_message(T("lang_switched_en"), T("lang_switched_en"), "cyan", duration=2.0)
        return True

    if choice.upper() == "S":
        show_settings_menu()
        return True

    modules_map = {
        "1": ("modules.cpu", "CPUOptimizer", "CPU"),
        "2": ("modules.gpu", "GPUOptimizer", "GPU"),
        "3": ("modules.thermal", "ThermalManager", "Thermal"),
        "4": ("modules.memory", "MemoryManager", "Memory"),
        "5": ("modules.system", "SystemTweaker", "System"),
        "6": ("modules.quick_tools", "QuickTools", "QuickTools"),
        "7": ("modules.monitor", "run_monitor", "Monitor"),
        "8": ("modules.magisk_module", "MagiskModuleBuilder", "Magisk"),
        "9": ("modules.img_tools", "IMGTools", "IMG Tools"),
        "10": ("modules.spoofing", "SpoofingCenter", "Spoofing"),
        "11": ("modules.network", "NetworkOptimizer", "Network"),
        "12": ("modules.app_manager", "AppManager", "App Manager"),
        "13": ("modules.kernel_tuner", "KernelTuner", "Kernel"),
        "14": ("modules.battery", "BatteryManager", "Battery"),
        "15": ("modules.anykernel3", "run", "AnyKernel3"),
    }

    if choice not in modules_map:
        popup_message(T("error"), T("invalid_choice"), "red", duration=2.0)
        return True

    module_path, class_name, display_name = modules_map[choice]

    try:
        console.clear()
        loading_spinner(f"{T('loading')} {display_name}...", 1.5)

        if choice == "7":
            from modules.monitor import run_monitor
            console.clear()
            run_monitor()
        else:
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            if isinstance(cls, type):
                # 类入口: 实例化 -> 调用 interactive_menu()
                instance = cls()
                instance.interactive_menu()
            else:
                # 函数入口: 直接调用 (如 run())
                cls()

    except Exception as e:
        log_exception("MAIN", e)
        popup_message(T("error"), f"{T('module_load_fail')}: {str(e)}", "red", duration=4.0)

    return True


# ============ 清理退出 ============
def cleanup():
    """清理并退出"""
    console.clear()
    animated_loading(T("env_cleanup"), 1.5)

    if state.selinux_permissive:
        shell.run("setenforce 1 2>/dev/null")

    console.clear()

    # 退出动画 - 烟花 + 滚动横幅
    firework(duration=1.5, bursts=3)
    console.clear()
    scrolling_banner(T("goodbye"), get_adaptive_width(), duration=2.0)

    log_file = get_log_file()
    if log_file:
        console.print(f"[dim]{T('log_file_label')}: {log_file}[/]")
    console.print()

    _show_cursor()
    sys.exit(0)


# ============ 信号处理 ============
def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    console.print()
    console.print(f"[yellow]{T('interrupt_signal')}[/]")
    cleanup()


# ============ 主入口 ============
def main():
    """主函数"""
    # 隐藏光标（动画期间不显示）
    _hide_cursor()

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)

    # 确保数据目录存在，清理上次缓存
    ensure_all_dirs()
    clean_tmp()

    # 加载持久化语言设置
    _load_language()

    try:
        # 启动动画
        show_splash_screen()

        # 免责协议
        if not is_disclaimer_accepted():
            if not show_disclaimer():
                _show_cursor()
                sys.exit(0)

        # 用户认证
        if not show_auth():
            _show_cursor()
            sys.exit(0)

        # 初始化环境
        init_environment()

        # 主循环
        running = True
        while running:
            console.clear()
            show_main_menu()

            console.print()
            choice = _ask(
                "[bold bright_cyan]" + T("please_select") + "[/]",
                choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "S", "s", "L", "l"],
                default="0"
            )

            if not handle_menu_choice(choice):
                running = False

        cleanup()

    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        log_exception("MAIN", e)
        console.clear()
        console.print(f"[bold red]{T('unexpected_error')}: {e}[/]")
        _wait_key(f"\n{T('press_any_key')}")
        cleanup()


if __name__ == "__main__":
    main()
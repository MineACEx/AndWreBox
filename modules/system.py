#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from core.shell import shell
from core.config import LOG_COLORS
from core.i18n import T
from core.utils import log_event, backup_config
from core.animations import (
    console, typewriter, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)


class SystemTweaker:
    """系统底层修改器"""

    # 常用build.prop优化项
    BUILD_PROP_TWEAKS = {
        "性能优化": {
            "debug.performance.tuning": "1",
            "video.accelerate.hw": "1",
            "persist.sys.composition.type": "gpu",
            "debug.sf.hw": "1",
            "hwui.render_dirty_regions": "false",
            "debug.composition.type": "gpu",
            "ro.config.hw_quickpoweron": "true",
        },
        "省电优化": {
            "wifi.supplicant_scan_interval": "300",
            "pm.sleep_mode": "1",
            "power.saving.mode": "1",
            "ro.ril.disable.power.collapse": "0",
            "ro.mot.eri.losalert.delay": "1000",
        },
        "触控优化": {
            "touch.pressure.scale": "0.001",
            "view.scroll_friction": "1.5",
            "ro.min_pointer_dur": "8",
            "ro.max.fling_velocity": "20000",
            "ro.min.fling_velocity": "10000",
        },
        "网络优化": {
            "net.tcp.buffersize.default": "4096,87380,256960,4096,16384,256960",
            "net.tcp.buffersize.wifi": "4096,87380,256960,4096,16384,256960",
            "net.tcp.buffersize.umts": "4096,87380,256960,4096,16384,256960",
            "net.ipv4.tcp_ecn": "0",
            "net.ipv4.route.flush": "1",
            "net.ipv4.tcp_rfc1337": "1",
            "net.ipv4.tcp_sack": "1",
            "net.ipv4.tcp_timestamps": "1",
            "net.ipv4.tcp_window_scaling": "1",
        },
        "Dalvik/ART优化": {
            "dalvik.vm.heapstartsize": "16m",
            "dalvik.vm.heapgrowthlimit": "256m",
            "dalvik.vm.heapsize": "512m",
            "dalvik.vm.heaptargetutilization": "0.75",
            "dalvik.vm.heapminfree": "2m",
            "dalvik.vm.heapmaxfree": "8m",
        },
    }

    # 广告域名列表
    AD_HOSTS = [
        "127.0.0.1 doubleclick.net",
        "127.0.0.1 googleadservices.com",
        "127.0.0.1 googlesyndication.com",
        "127.0.0.1 google-analytics.com",
        "127.0.0.1 adservice.google.com",
        "127.0.0.1 pagead2.googlesyndication.com",
        "127.0.0.1 admob.com",
        "127.0.0.1 ads.facebook.com",
        "127.0.0.1 graph.facebook.com",
        "127.0.0.1 analytics.twitter.com",
        "127.0.0.1 ads.twitter.com",
        "127.0.0.1 api.umeng.com",
        "127.0.0.1 alog.umeng.com",
        "127.0.0.1 oc.umeng.com",
        "127.0.0.1 ad.umeng.com",
        "127.0.0.1 stats.umeng.com",
        "127.0.0.1 mobile.umeng.com",
        "127.0.0.1 mmstat.com",
        "127.0.0.1 ad.360in.com",
        "127.0.0.1 ad.xiaomi.com",
        "127.0.0.1 ad.mi.com",
        "127.0.0.1 tracking.miui.com",
        "127.0.0.1 api.ad.xiaomi.com",
        "127.0.0.1 sdkconfig.ad.xiaomi.com",
        "127.0.0.1 new.api.ad.xiaomi.com",
        "127.0.0.1 ad.oppomobile.com",
        "127.0.0.1 adx.ads.oppomobile.com",
        "127.0.0.1 adsfs.oppomobile.com",
        "127.0.0.1 adapi.vivo.com.cn",
        "127.0.0.1 adx.vivo.com.cn",
        "127.0.0.1 ads.meizu.com",
        "127.0.0.1 ad.huawei.com",
        "127.0.0.1 analytics.huawei.com",
        "127.0.0.1 appsflyer.com",
        "127.0.0.1 adjust.com",
        "127.0.0.1 branch.io",
        "127.0.0.1 bytedance.com",
        "127.0.0.1 pangle.io",
        "127.0.0.1 pangleglobal.com",
        "127.0.0.1 unityads.unity3d.com",
        "127.0.0.1 applovin.com",
        "127.0.0.1 ironsrc.mobi",
        "127.0.0.1 vungle.com",
        "127.0.0.1 chartboost.com",
        "127.0.0.1 inmobi.com",
        "127.0.0.1 flurry.com",
        "127.0.0.1 crashlytics.com",
        "127.0.0.1 fabric.io",
        "127.0.0.1 moatads.com",
        "127.0.0.1 mopub.com",
        "127.0.0.1 tapjoy.com",
        "127.0.0.1 supersonicads.com",
        "127.0.0.1 fyber.com",
        "127.0.0.1 pubmatic.com",
        "127.0.0.1 openx.net",
        "127.0.0.1 rubiconproject.com",
        "127.0.0.1 casalemedia.com",
        "127.0.0.1 adsrvr.org",
        "127.0.0.1 criteo.com",
        "127.0.0.1 smartadserver.com",
        "127.0.0.1 sovrn.com",
        "127.0.0.1 indexww.com",
        "127.0.0.1 adnxs.com",
        "127.0.0.1 contextweb.com",
        "127.0.0.1 spotxchange.com",
        "127.0.0.1 tremorhub.com",
        "127.0.0.1 springserve.com",
        "127.0.0.1 mfadsrvr.com",
        "127.0.0.1 adsafeprotected.com",
        "127.0.0.1 bidswitch.net",
        "127.0.0.1 adkernel.com",
        "127.0.0.1 adcolony.com",
        "127.0.0.1 vungle.akadns.net",
        "127.0.0.1 startapp.com",
        "127.0.0.1 startappservice.com",
        "127.0.0.1 mintegral.com",
        "127.0.0.1 rayjump.com",
    ]

    def show_status(self):
        """显示系统修改状态"""
        title_panel(T("system_status"), T("build.prop | hosts | 进程 | 日志"))

        # build.prop状态
        build_size = shell.run_raw("wc -c < /system/build.prop 2>/dev/null").strip()
        console.print(f"  [cyan]{T('build.prop大小:')}[/] {build_size} bytes")

        # hosts状态
        hosts_size = shell.run_raw("wc -c < /system/etc/hosts 2>/dev/null").strip()
        hosts_lines = shell.run_raw("wc -l < /system/etc/hosts 2>/dev/null").strip()
        console.print(f"  [cyan]{T('hosts大小:')}[/] {hosts_size} bytes  [cyan]{T('行数:')}[/] {hosts_lines}")

        # 进程数
        proc_count = shell.run_raw("ps -A | wc -l").strip()
        console.print(f"  [cyan]{T('运行进程数:')}[/] {proc_count}")

        # 日志大小
        log_size = shell.run_raw("du -sh /data/logs 2>/dev/null || echo 'N/A'").strip()
        console.print(f"  [cyan]{T('日志目录大小:')}[/] {log_size}")

        divider()

    def apply_build_prop_tweaks(self, category: str = None):
        """应用build.prop优化"""
        if category and category in self.BUILD_PROP_TWEAKS:
            tweaks = self.BUILD_PROP_TWEAKS[category]
        else:
            tweaks = {}
            for cat_tweaks in self.BUILD_PROP_TWEAKS.values():
                tweaks.update(cat_tweaks)

        loading_spinner(T("正在挂载/system为可读写"), 1.0)
        shell.remount_rw("system")

        loading_spinner(T("正在应用build.prop优化 ({0}项)").format(len(tweaks)), 1.5)

        success_count = 0
        with gradient_progress(len(tweaks), "应用build.prop优化") as (progress, task):
            for prop, value in tweaks.items():
                if shell.set_prop(prop, value):
                    success_count += 1
                progress.update(task, advance=1)

        popup_message(T("完成"), T("build.prop优化完成 ({0}/{1})").format(success_count, len(tweaks)), "green")
        log_event("SUCCESS", "SYSTEM", f"build.prop优化: {category or 'all'} ({success_count}/{len(tweaks)})")

    def show_build_prop_categories(self):
        """显示所有build.prop分类"""
        console.clear()
        title_panel(T("build.prop 优化分类"), "")
        for i, (cat, tweaks) in enumerate(self.BUILD_PROP_TWEAKS.items(), 1):
            console.print(f"  [bold cyan]{i}.[/] {cat} [dim]({len(tweaks)}项)[/]")
        console.print(f"  [bold cyan]{len(self.BUILD_PROP_TWEAKS)+1}.[/] {T('system_bp_apply_all')}")

    def apply_hosts_adblock(self):
        """应用hosts广告拦截"""
        loading_spinner(T("正在挂载/system为可读写"), 1.0)
        shell.remount_rw("system")

        # 备份原始hosts
        shell.run("cp /system/etc/hosts /system/etc/hosts.bak 2>/dev/null")

        loading_spinner(T("正在写入广告拦截规则"), 1.5)

        # 构建hosts内容
        hosts_content = "127.0.0.1 localhost\n::1 localhost\n\n# === Android Root Toolbox AdBlock ===\n"
        hosts_content += "\n".join(self.AD_HOSTS)

        # 写入hosts - 使用安全的write_file方法
        shell.write_file("/data/local/tmp/hosts_new", hosts_content)
        shell.run("cp /data/local/tmp/hosts_new /system/etc/hosts")
        shell.run("chmod 644 /system/etc/hosts")

        popup_message(T("完成"), T("广告拦截已启用 ({0}条规则)").format(len(self.AD_HOSTS)), "green")
        log_event("SUCCESS", "SYSTEM", f"hosts广告拦截: {len(self.AD_HOSTS)}条规则")

    def remove_hosts_adblock(self):
        """移除hosts广告拦截"""
        shell.remount_rw("system")
        shell.run("cp /system/etc/hosts.bak /system/etc/hosts 2>/dev/null")
        shell.run("chmod 644 /system/etc/hosts")
        popup_message(T("完成"), T("广告拦截已移除，hosts已恢复"), "green")

    def trim_system_processes(self):
        """精简冗余系统进程"""
        loading_spinner(T("正在扫描可精简进程"), 1.5)

        # 可安全禁用/冻结的进程列表
        bloatware = [
            "com.facebook.appmanager",
            "com.facebook.system",
            "com.facebook.services",
            "com.google.android.apps.maps",
            "com.google.android.apps.photos",
            "com.google.android.apps.docs",
            "com.google.android.apps.tachyon",  # Duo
            "com.google.android.videos",
            "com.google.android.music",
            "com.google.android.apps.youtube.music",
            "com.android.chrome",
            "com.google.android.gm",
            "com.google.android.googlequicksearchbox",
            "com.google.android.apps.wellbeing",
            "com.google.android.printservice.recommendation",
            "com.google.android.projection.gearhead",
            "com.android.bookmarkprovider",
            "com.android.printspooler",
            "com.android.wallpaper.livepicker",
            "com.android.dreams.basic",
            "com.android.dreams.phototable",
            "com.android.managedprovisioning",
            "com.android.traceur",
            "com.android.hotwordenrollment",
        ]

        disabled_count = 0
        with gradient_progress(len(bloatware), "精简系统进程") as (progress, task):
            for pkg in bloatware:
                ok, out, _ = shell.run(f"pm disable {pkg} 2>/dev/null")
                if ok or "disabled" in out.lower():
                    disabled_count += 1
                progress.update(task, advance=1)

        popup_message(T("完成"), T("已精简 {0}/{1} 个冗余进程").format(disabled_count, len(bloatware)), "green")
        log_event("SUCCESS", "SYSTEM", f"精简进程: {disabled_count}/{len(bloatware)}")

    def throttle_logging(self, enable: bool = True):
        """日志系统节流"""
        if enable:
            shell.set_prop("log.tag.stats_log", "ERROR")
            shell.set_prop("log.tag.snet_event_log", "ERROR")
            shell.set_prop("log.tag.APM_AudioPolicyManager", "ERROR")
            shell.set_prop("ro.logd.size", "256K")
            shell.set_prop("persist.logd.size", "256K")
            shell.set_prop("ro.logd.kernel", "false")
            shell.set_prop("persist.logd.size.crash", "64K")
            shell.set_prop("persist.logd.size.main", "256K")
            shell.set_prop("persist.logd.size.system", "64K")
            shell.set_prop("persist.logd.size.radio", "64K")
            shell.run("setprop ctl.start logd-reexec 2>/dev/null")
            popup_message(T("完成"), T("system_log_throttled"), "green")
        else:
            shell.set_prop("ro.logd.size", "1M")
            shell.set_prop("persist.logd.size", "1M")
            shell.set_prop("ro.logd.kernel", "true")
            shell.run("setprop ctl.start logd-reexec 2>/dev/null")
            popup_message(T("完成"), T("system_log_restored"), "green")

    def interactive_menu(self):
        """系统修改交互菜单"""
        while True:
            console.clear()
            title_panel(T("system_title"), T("system_subtitle"))
            self.show_status()

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('system_buildprop')}      [bold cyan]2.[/] {T('system_hosts_adblock')}")
            console.print(f"  [bold cyan]3.[/] {T('system_remove_adblock')}        [bold cyan]4.[/] {T('system_debloat')}")
            console.print(f"  [bold cyan]5.[/] {T('system_log_throttle')}        [bold cyan]6.[/] {T('system_log_restore')}")
            console.print(f"  [bold cyan]0.[/] {T('back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]", choices=["0","1","2","3","4","5","6"], default="0")

            if choice == "0":
                break
            elif choice == "1":
                self.show_build_prop_categories()
                cats = list(self.BUILD_PROP_TWEAKS.keys())
                n = int(Prompt.ask(T("选择分类"), choices=[str(i) for i in range(1, len(cats)+2)], default="6"))
                if n <= len(cats):
                    self.apply_build_prop_tweaks(cats[n-1])
                else:
                    self.apply_build_prop_tweaks()
                input(T("press_any_key"))
            elif choice == "2":
                if Confirm.ask(T("将应用hosts广告拦截规则，继续?"), default=True):
                    self.apply_hosts_adblock()
                input(T("press_any_key"))
            elif choice == "3":
                if Confirm.ask(T("移除广告拦截规则?"), default=True):
                    self.remove_hosts_adblock()
                input(T("press_any_key"))
            elif choice == "4":
                if Confirm.ask(T("将精简冗余系统进程，继续?"), default=True):
                    self.trim_system_processes()
                input(T("press_any_key"))
            elif choice == "5":
                if Confirm.ask(T("启用日志节流? (省电)"), default=True):
                    self.throttle_logging(True)
                input(T("press_any_key"))
            elif choice == "6":
                if Confirm.ask(T("恢复日志系统默认?"), default=True):
                    self.throttle_logging(False)
                input(T("press_any_key"))
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
IMG 镜像工具箱 - 解包/打包/信息查看/刷入
支持: boot.img | system.img | vendor.img | recovery.img | dtbo.img
"""

import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box

from core.shell import shell
from core.i18n import T
from core.animations import (
    console, loading_spinner, gradient_progress,
    popup_message, divider, title_panel
)
from core.utils import log_event

# IMG工具输出目录
IMG_OUTPUT_DIR = "/sdcard/AndroidRootToolbox/img_tools"


class IMGTools:
    """IMG镜像工具箱"""

    def __init__(self):
        self.output_dir = IMG_OUTPUT_DIR
        shell.mkdir(self.output_dir)
        self._check_tools()

    def _check_tools(self) -> bool:
        """检查必要工具"""
        self.tools = {
            "magiskboot": shell.cmd_exists("magiskboot"),
            "simg2img": shell.cmd_exists("simg2img"),
            "img2simg": shell.cmd_exists("img2simg"),
            "unpackbootimg": shell.cmd_exists("unpackbootimg"),
            "mkbootimg": shell.cmd_exists("mkbootimg"),
            "file": shell.cmd_exists("file"),
            "dd": shell.cmd_exists("dd"),
            "hexdump": shell.cmd_exists("hexdump") or shell.cmd_exists("xxd"),
        }

        # 如果没有magiskboot，尝试从Magisk目录找
        if not self.tools["magiskboot"]:
            ok, out, _ = shell.run("find /data/adb -name 'magiskboot' -type f 2>/dev/null | head -1")
            if ok and out.strip():
                self.tools["magiskboot"] = True
                self._magiskboot_path = out.strip()
            else:
                self._magiskboot_path = "magiskboot"

        return any(self.tools.values())

    def _get_img_info(self, img_path: str) -> dict:
        """获取IMG镜像信息"""
        info = {
            "path": img_path,
            "size": 0,
            "format": "unknown",
            "type": "unknown",
        }

        # 文件大小
        ok, out, _ = shell.run(f"ls -la '{img_path}' 2>/dev/null | awk '{{print $5}}'")
        if ok and out.strip().isdigit():
            size = int(out.strip())
            if size > 1048576:
                info["size"] = f"{size / 1048576:.1f} MB"
            else:
                info["size"] = f"{size / 1024:.0f} KB"

        # 文件类型
        ok, out, _ = shell.run(f"file '{img_path}' 2>/dev/null")
        if ok:
            if "Android bootimg" in out:
                info["type"] = "boot.img"
                info["format"] = "Android Boot Image"
            elif "Android sparse image" in out:
                info["format"] = "Android Sparse Image"
                info["type"] = "sparse_img"
            elif "ext4" in out.lower():
                info["format"] = "EXT4 Filesystem"
                info["type"] = "ext4_img"
            elif "erofs" in out.lower():
                info["format"] = "EROFS Filesystem"
                info["type"] = "erofs_img"
            elif "data" in out.lower():
                info["format"] = "Raw Data"
                info["type"] = "raw_img"
            else:
                info["format"] = out.strip()

        # 如果是boot.img，获取更多信息
        if info["type"] == "boot.img":
            ok, out, _ = shell.run(f"file {img_path} 2>/dev/null")
            # 提取内核版本
            ok2, kernel_ver, _ = shell.run(
                f"strings {img_path} 2>/dev/null | grep 'Linux version' | head -1"
            )
            if ok2 and kernel_ver:
                info["kernel"] = kernel_ver.strip()

        return info

    def show_img_info(self, img_path: str = None):
        """显示IMG镜像详细信息"""
        if not img_path:
            img_path = Prompt.ask(f"[cyan]{T('img_select_file')}[/]")

        if not shell.file_exists(img_path):
            popup_message(T("error"), T("img_file_not_found").format(file=img_path), "red")
            return

        info = self._get_img_info(img_path)

        title_panel(T("img_info"), img_path)

        table = Table(border_style="cyan", box=box.ROUNDED, show_header=False)
        table.add_column(T("img_item"), style="cyan", width=16)
        table.add_column(T("img_value"), style="white", width=50)

        table.add_row(T("img_info_size"), info["size"])
        table.add_row(T("img_info_format"), info["format"])
        table.add_row(T("img_type"), info["type"])

        if "kernel" in info:
            table.add_row(T("img_info_kernel"), info["kernel"])

        console.print(table)

        # 如果是boot.img，显示更多详情
        if info["type"] == "boot.img" and self.tools["magiskboot"]:
            console.print()
            loading_spinner(T("img_analyzing_boot"), 1.5)
            mb = self._get_magiskboot()
            ok, out, _ = shell.run(f"{mb} unpack -n '{img_path}' 2>&1 | head -20")
            if ok:
                console.print(out)

    def _get_magiskboot(self) -> str:
        """获取magiskboot路径"""
        if hasattr(self, '_magiskboot_path'):
            return self._magiskboot_path
        return "magiskboot"

    def unpack_boot(self, img_path: str = None):
        """解包boot.img"""
        if not img_path:
            img_path = Prompt.ask(f"[cyan]{T('img_select_file')}[/]")

        if not shell.file_exists(img_path):
            popup_message(T("error"), T("img_file_not_found").format(file=img_path), "red")
            return

        info = self._get_img_info(img_path)
        if info["type"] != "boot.img":
            popup_message(T("warning"), T("img_not_boot_img"), "yellow")
            if not Confirm.ask(T("img_continue_anyway"), default=False):
                return

        # 创建输出目录
        img_name = os.path.basename(img_path).replace(".img", "")
        output_dir = f"{self.output_dir}/{img_name}_unpacked"
        shell.mkdir(output_dir)

        loading_spinner(T("img_unpacking").format(file=os.path.basename(img_path)), 2.0)

        mb = self._get_magiskboot()

        # 尝试用magiskboot解包
        ok, out, err = shell.run(
            f"(cd '{output_dir}' && {mb} unpack '{img_path}' 2>&1)",
            timeout=30
        )

        if not ok:
            # 尝试用unpackbootimg解包
            ok2, out2, err2 = shell.run(
                f"(cd '{output_dir}' && unpackbootimg -i '{img_path}' 2>&1)",
                timeout=30
            )
            if not ok2:
                # 手动提取
                shell.run(f"cp '{img_path}' '{output_dir}/'")
                popup_message(T("warning"),
                              T("img_auto_unpack_failed").format(dir=output_dir, path=img_path),
                              "yellow")
                return
            else:
                out = out2

        # 列出解包结果
        shell.run(f"ls -la {output_dir}/")
        console.print(f"\n[green]{T('img_unpacked_files')}[/]")
        ok, files, _ = shell.run(f"ls -lh {output_dir}/")
        if ok:
            console.print(files)

        popup_message(T("success"),
                      f"{T('img_unpack_ok')}\n{output_dir}/",
                      "green")
        log_event("SUCCESS", "IMG", f"解包boot.img: {img_path} -> {output_dir}")

    def repack_boot(self, unpack_dir: str = None, output_path: str = None):
        """打包boot.img"""
        if not unpack_dir:
            unpack_dir = Prompt.ask(f"[cyan]{T('img_unpacked_dir')}[/]")

        if not output_path:
            output_path = f"{self.output_dir}/repacked_boot.img"

        mb = self._get_magiskboot()

        loading_spinner(T("img_repacking"), 2.0)

        ok, out, err = shell.run(
            f"cd {unpack_dir} && {mb} repack {unpack_dir} {output_path} 2>&1",
            timeout=30
        )

        if not ok:
            # 尝试用mkbootimg
            ok2, out2, err2 = shell.run(
                f"mkbootimg --kernel {unpack_dir}/kernel "
                f"--ramdisk {unpack_dir}/ramdisk.cpio "
                f"--output {output_path} 2>&1",
                timeout=30
            )
            if not ok2:
                popup_message(T("error"),
                              T("img_repack_failed").format(err=err, err2=err2),
                              "red")
                return

        popup_message(T("success"),
                      f"{T('img_repack_ok')}\n{output_path}",
                      "green")
        log_event("SUCCESS", "IMG", f"打包boot.img: {output_path}")

    def extract_img(self, img_path: str = None, mount_point: str = None):
        """提取任意img镜像内容"""
        if not img_path:
            img_path = Prompt.ask(f"[cyan]{T('img_select_file')}[/]")

        if not shell.file_exists(img_path):
            popup_message(T("error"), T("img_file_not_found").format(file=img_path), "red")
            return

        img_name = os.path.basename(img_path).replace(".img", "")
        output_dir = f"{self.output_dir}/{img_name}_extracted"
        shell.mkdir(output_dir)

        info = self._get_img_info(img_path)

        loading_spinner(T("img_extracting").format(file=os.path.basename(img_path)), 2.0)

        if info["format"] == "Android Sparse Image":
            # 转换为raw镜像
            raw_img = f"{output_dir}/{img_name}_raw.img"
            console.print(f"[cyan]{T('img_converting_sparse')}[/]")
            ok, out, err = shell.run(f"simg2img {img_path} {raw_img} 2>&1", timeout=60)
            if ok:
                img_path = raw_img

        # 尝试挂载并复制
        mount_pt = mount_point or f"/data/local/tmp/mnt_{img_name}"
        shell.mkdir(mount_pt)

        ok, out, err = shell.run(f"mount -o ro,loop '{img_path}' '{mount_pt}' 2>&1", timeout=10)
        if ok:
            shell.run(f"cp -r '{mount_pt}'/* '{output_dir}/' 2>/dev/null")
            shell.run(f"umount '{mount_pt}' 2>/dev/null")
        else:
            # 如果挂载失败，尝试直接复制
            shell.run(f"cp '{img_path}' '{output_dir}/'")

        # 列出输出
        ok, files, _ = shell.run(f"ls -lh {output_dir}/")
        if ok:
            console.print(f"\n[green]{T('img_extracted_files')}[/]")
            console.print(files)

        popup_message(T("success"),
                      f"{T('img_unpack_ok')}\n{output_dir}/",
                      "green")
        log_event("SUCCESS", "IMG", f"提取镜像: {img_path}")

    def flash_img(self, img_path: str = None, partition: str = None):
        """刷入IMG镜像 - 危险操作！"""
        if not img_path:
            img_path = Prompt.ask(f"[cyan]{T('img_select_file')}[/]")

        if not partition:
            # 列出可用分区
            ok, parts, _ = shell.run(
                "ls /dev/block/bootdevice/by-name/ 2>/dev/null || "
                "ls /dev/block/by-name/ 2>/dev/null"
            )
            console.print(f"\n[cyan]{T('img_available_partitions')}[/]")
            if ok:
                console.print(parts)
            partition = Prompt.ask(f"[cyan]{T('img_target_partition')}[/]")

        # 确认警告
        console.print()
        console.print(f"[bold red]{T('img_flash_warn')}[/]")
        console.print(f"[yellow]{T('img_flash_image_info').format(path=img_path)}[/]")
        console.print(f"[yellow]{T('img_flash_partition_info').format(name=partition)}[/]")
        console.print()

        if not Confirm.ask(f"[bold red]{T('img_flash_confirm')}[/]", default=False):
            return

        if not Confirm.ask(f"[bold red]{T('img_flash_type_yes')}[/]", default=False):
            return

        # 确认分区路径
        part_path = shell.get_partition_path(partition)
        if not part_path:
            popup_message(T("error"), T("img_partition_not_found").format(name=partition), "red")
            return

        loading_spinner(T("img_flashing").format(name=partition), 2.0)

        ok, out, err = shell.dd_flash(img_path, partition)
        if ok:
            popup_message(T("success"),
                          T("img_flash_complete").format(name=partition),
                          "green")
            log_event("SUCCESS", "IMG", f"刷入镜像: {partition}")
        else:
            popup_message(T("error"), T("img_flash_failed").format(err=err), "red")

    def dump_partition(self, partition: str = None, output_path: str = None):
        """备份分区为IMG"""
        if not partition:
            ok, parts, _ = shell.run(
                "ls /dev/block/bootdevice/by-name/ 2>/dev/null || "
                "ls /dev/block/by-name/ 2>/dev/null"
            )
            console.print(f"\n[cyan]{T('img_available_partitions')}[/]")
            if ok:
                console.print(parts)
            partition = Prompt.ask(f"[cyan]{T('img_partition_to_dump')}[/]")

        part_path = shell.get_partition_path(partition)
        if not part_path:
            popup_message(T("error"), T("img_partition_not_found").format(name=partition), "red")
            return

        if not output_path:
            output_path = f"{self.output_dir}/{partition}_dump.img"

        loading_spinner(T("img_dumping").format(name=partition), 2.0)

        ok, out, err = shell.run(f"dd if={part_path} of={output_path} bs=4096 2>&1")
        if ok:
            popup_message(T("success"),
                          T("img_dump_complete").format(path=output_path),
                          "green")
            log_event("SUCCESS", "IMG", f"备份分区: {partition}")
        else:
            popup_message(T("error"), T("img_dump_failed").format(err=err), "red")

    def interactive_menu(self):
        """IMG工具交互菜单"""
        while True:
            console.clear()
            title_panel(T("img_title"), T("img_subtitle"))

            console.print()
            console.print(f"  [bold cyan]1.[/] {T('img_unpack_boot')}")
            console.print(f"  [bold cyan]2.[/] {T('img_repack_boot')}")
            console.print(f"  [bold cyan]3.[/] {T('img_extract_any')} (system/vendor/...)")
            console.print(f"  [bold cyan]4.[/] {T('img_info')}")
            console.print(f"  [bold cyan]5.[/] [bold red]{T('img_flash')}[/]")
            console.print(f"  [bold cyan]6.[/] {T('img_dump_partition_menu')}")
            console.print(f"  [bold cyan]0.[/] {T('back')}")
            divider()

            choice = Prompt.ask(f"[bold]{T('please_select')}[/]", default="0")

            if choice == "0":
                break
            elif choice == "1":
                if Confirm.ask(f"[cyan]{T('img_use_file_browser')}[/]", default=True):
                    files = shell.file_browser("/sdcard", "*.img")
                    if files:
                        console.print(f"\n[cyan]{T('img_found_files')}[/]")
                        for i, f in enumerate(files, 1):
                            console.print(f"  [cyan]{i}.[/] {f}")
                        idx = Prompt.ask(f"[bold]{T('img_select_file_idx')}[/]", default="1")
                        try:
                            img = files[int(idx)-1]
                        except (ValueError, IndexError):
                            img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                    else:
                        img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                else:
                    img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                self.unpack_boot(img)
                input(f"\n{T('press_any_key')}")
            elif choice == "2":
                d = Prompt.ask(f"[cyan]{T('img_unpacked_dir')}[/]",
                               default=f"{IMG_OUTPUT_DIR}/boot_unpacked")
                out = Prompt.ask(f"[cyan]{T('img_output_dir')}[/]",
                                 default=f"{IMG_OUTPUT_DIR}/repacked_boot.img")
                self.repack_boot(d, out)
                input(f"\n{T('press_any_key')}")
            elif choice == "3":
                if Confirm.ask(f"[cyan]{T('img_use_file_browser')}[/]", default=True):
                    files = shell.file_browser("/sdcard", "*.img")
                    if files:
                        console.print(f"\n[cyan]{T('img_found_files')}[/]")
                        for i, f in enumerate(files, 1):
                            console.print(f"  [cyan]{i}.[/] {f}")
                        idx = Prompt.ask(f"[bold]{T('img_select_file_idx')}[/]", default="1")
                        try:
                            img = files[int(idx)-1]
                        except (ValueError, IndexError):
                            img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/system.img")
                    else:
                        img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/system.img")
                else:
                    img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/system.img")
                self.extract_img(img)
                input(f"\n{T('press_any_key')}")
            elif choice == "4":
                if Confirm.ask(f"[cyan]{T('img_use_file_browser')}[/]", default=True):
                    files = shell.file_browser("/sdcard", "*.img")
                    if files:
                        console.print(f"\n[cyan]{T('img_found_files')}[/]")
                        for i, f in enumerate(files, 1):
                            console.print(f"  [cyan]{i}.[/] {f}")
                        idx = Prompt.ask(f"[bold]{T('img_select_file_idx')}[/]", default="1")
                        try:
                            img = files[int(idx)-1]
                        except (ValueError, IndexError):
                            img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                    else:
                        img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                else:
                    img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                self.show_img_info(img)
                input(f"\n{T('press_any_key')}")
            elif choice == "5":
                if Confirm.ask(f"[cyan]{T('img_use_file_browser')}[/]", default=True):
                    files = shell.file_browser("/sdcard", "*.img")
                    if files:
                        console.print(f"\n[cyan]{T('img_found_files')}[/]")
                        for i, f in enumerate(files, 1):
                            console.print(f"  [cyan]{i}.[/] {f}")
                        idx = Prompt.ask(f"[bold]{T('img_select_file_idx')}[/]", default="1")
                        try:
                            img = files[int(idx)-1]
                        except (ValueError, IndexError):
                            img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                    else:
                        img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                else:
                    img = Prompt.ask(f"[cyan]{T('img_select_file')}[/]", default="/sdcard/boot.img")
                self.flash_img(img)
                input(f"\n{T('press_any_key')}")
            elif choice == "6":
                self.dump_partition()
                input(f"\n{T('press_any_key')}")
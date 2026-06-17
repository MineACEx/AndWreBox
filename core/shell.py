#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox Shell命令执行器 - 通过su执行root命令
v1.0: su -c sh + stdin管道，彻底根治引号逃逸
"""

import subprocess
import os
import re
import time
import uuid
from typing import Tuple, Optional, List


class ShellExecutor:
    """Root Shell命令执行器，所有底层操作通过su -c执行"""

    def __init__(self):
        self._root_available = False
        self._root_method = ""
        self._check_root()

    def _check_root(self) -> bool:
        """检测Root权限"""
        try:
            # 检测su二进制
            result = subprocess.run(
                ["which", "su"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                # 测试su权限
                test = subprocess.run(
                    ["su", "-c", "id"],
                    capture_output=True, text=True, timeout=5
                )
                if "uid=0" in test.stdout or "uid=0" in test.stderr:
                    self._root_available = True
                    self._root_method = self._detect_root_method()
                    return True
            return False
        except Exception:
            return False

    def _detect_root_method(self) -> str:
        """检测Root方案"""
        try:
            # 检测Magisk
            r = self.run_raw("magisk -c 2>/dev/null || echo 'no_magisk'")
            if "no_magisk" not in r:
                return "Magisk"
            # 检测KernelSU
            r = self.run_raw("ksud -V 2>/dev/null || echo 'no_ksu'")
            if "no_ksu" not in r:
                return "KernelSU"
            return "Unknown"
        except Exception:
            return "Unknown"

    @property
    def has_root(self) -> bool:
        return self._root_available

    @property
    def root_method(self) -> str:
        return self._root_method

    def run(self, command: str, timeout: int = 10) -> Tuple[bool, str, str]:
        """
        执行root命令 — v3.2.3: 通过stdin管道传给 su -c sh，彻底消除引号逃逸
        返回: (成功标志, 标准输出, 标准错误)
        """
        if not self._root_available:
            return False, "", "Root权限不可用"

        try:
            # 命令通过stdin传给sh，不经过su -c的参数解析，彻底避免引号问题
            result = subprocess.run(
                ["su", "-c", "sh"],
                input=command,
                capture_output=True, text=True, timeout=timeout,
                shell=False
            )
            return (
                result.returncode == 0,
                result.stdout.strip(),
                result.stderr.strip()
            )
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)

    def run_raw(self, command: str, timeout: int = 10) -> str:
        """执行命令并返回合并输出"""
        ok, out, err = self.run(command, timeout)
        return out if ok else f"{out}\n{err}".strip()

    def run_stdin(self, command: str, stdin_data: str, timeout: int = 10) -> Tuple[bool, str, str]:
        """
        通过stdin管道安全输入数据执行命令 — v3.2.3: heredoc + su -c sh
        用法: shell.run_stdin("cat > '/path/file'", content)
        """
        if not self._root_available:
            return False, "", "Root权限不可用"

        try:
            # 使用随机heredoc分隔符，避免内容冲突
            delim = f"TOOLBOX_EOF_{uuid.uuid4().hex[:8]}"
            # 构建完整脚本: command << 'DELIM' \n data \n DELIM
            full_input = f"{command} << '{delim}'\n{stdin_data}\n{delim}\n"
            result = subprocess.run(
                ["su", "-c", "sh"],
                input=full_input,
                capture_output=True, text=True, timeout=timeout,
                shell=False
            )
            return (
                result.returncode == 0,
                result.stdout.strip(),
                result.stderr.strip()
            )
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)

    def write_file(self, path: str, content: str) -> bool:
        """
        安全写入文件内容 — v3.2.3: heredoc + su -c sh，彻底根治
        """
        if not content:
            return False
        
        # 确保目标目录存在
        target_dir = os.path.dirname(path)
        if target_dir:
            self.mkdir(target_dir)
        
        ok, _, _ = self.run_stdin(f"cat > '{path}' 2>&1", content)
        if ok:
            self.run(f"chmod 644 '{path}' 2>/dev/null")
        
        return ok

    def write_file_multi(self, files: dict) -> bool:
        """
        批量写入多个文件 — 一次su调用完成所有写入
        files: {path: content, ...}
        """
        if not files:
            return False
        
        import uuid as _uuid
        delim = f"TOOLBOX_EOF_{_uuid.uuid4().hex[:8]}"
        script = ""
        for path, content in files.items():
            if not content:
                continue
            target_dir = os.path.dirname(path)
            if target_dir:
                script += f"mkdir -p '{target_dir}' 2>/dev/null\n"
            script += f"cat > '{path}' << '{delim}'\n{content}\n{delim}\n"
        
        ok, _, _ = self.run(script)
        return ok

    def write_node(self, path: str, value: str) -> bool:
        """写入sysfs节点 - 使用run_stdin安全写入，避免引号逃逸"""
        if not value:
            return False
        ok, _, err = self.run_stdin(f"cat > '{path}' 2>&1", value)
        if not ok:
            # 尝试chmod后写入
            self.run(f"chmod 644 '{path}' 2>/dev/null")
            ok, _, err = self.run_stdin(f"cat > '{path}' 2>&1", value)
        return ok

    def read_node(self, path: str) -> str:
        """读取sysfs节点"""
        ok, out, _ = self.run(f"cat '{path}' 2>/dev/null")
        return out.strip() if ok and out else ""

    def read_node_int(self, path: str) -> int:
        """读取整数节点值"""
        val = self.read_node(path)
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def file_exists(self, path: str) -> bool:
        """检查文件是否存在 (支持root路径)"""
        ok, out, _ = self.run(f"test -f '{path}' && echo 'EXISTS' || echo 'NOT_FOUND'")
        return ok and "EXISTS" in out

    def dir_exists(self, path: str) -> bool:
        """检查目录是否存在"""
        ok, out, _ = self.run(f"test -d '{path}' && echo 'EXISTS' || echo 'NOT_FOUND'")
        return ok and "EXISTS" in out

    def set_selinux_permissive(self) -> bool:
        """临时关闭SELinux"""
        return self.run("setenforce 0 2>/dev/null")[0]

    def remount_rw(self, partition: str) -> bool:
        """挂载分区为可读写"""
        return self.run(
            f"mount -o rw,remount '{partition}' 2>/dev/null || "
            f"mount -o rw,remount /dev/block/bootdevice/by-name/{partition} /{partition} 2>/dev/null"
        )[0]

    def get_prop(self, prop: str) -> str:
        """获取系统属性"""
        ok, out, _ = self.run(f"getprop {prop}")
        return out.strip() if ok else ""

    def set_prop(self, prop: str, value: str) -> bool:
        """设置系统属性"""
        return self.run(f"resetprop {prop} {value} 2>/dev/null || setprop {prop} {value} 2>/dev/null")[0]

    def ls(self, path: str, pattern: str = "*") -> List[str]:
        """列出文件"""
        ok, out, _ = self.run(f"ls '{path}'/{pattern} 2>/dev/null")
        return out.split("\n") if ok and out else []

    def find_files(self, path: str, name: str) -> List[str]:
        """查找文件"""
        ok, out, _ = self.run(f"find '{path}' -name '{name}' -type f 2>/dev/null")
        return out.split("\n") if ok and out else []

    def mkdir(self, path: str) -> bool:
        """创建目录"""
        return self.run(f"mkdir -p '{path}' 2>/dev/null")[0]

    def cp(self, src: str, dst: str) -> bool:
        """复制文件"""
        return self.run(f"cp -r '{src}' '{dst}' 2>/dev/null")[0]

    def rm(self, path: str) -> bool:
        """删除文件/目录"""
        return self.run(f"rm -rf '{path}' 2>/dev/null")[0]

    def chmod(self, path: str, mode: str) -> bool:
        """修改权限"""
        return self.run(f"chmod {mode} '{path}' 2>/dev/null")[0]

    def dd_flash(self, img_path: str, partition: str) -> bool:
        """使用dd刷入镜像（危险操作）"""
        return self.run(f"dd if='{img_path}' of=/dev/block/bootdevice/by-name/{partition} bs=4096 2>/dev/null")[0]

    def get_partition_path(self, partition: str) -> str:
        """获取分区路径"""
        ok, out, _ = self.run(
            f"ls /dev/block/bootdevice/by-name/{partition} 2>/dev/null || "
            f"ls /dev/block/by-name/{partition} 2>/dev/null || "
            f"echo 'NOT_FOUND'"
        )
        return out.strip() if ok and "NOT_FOUND" not in out else ""

    def get_block_size(self, path: str) -> int:
        """获取块设备大小"""
        ok, out, _ = self.run(f"blockdev --getsize64 {path} 2>/dev/null")
        return int(out.strip()) if ok and out.strip().isdigit() else 0

    def cmd_exists(self, cmd: str) -> bool:
        """检查命令是否存在"""
        ok, out, _ = self.run(f"which {cmd} 2>/dev/null || echo 'NOT_FOUND'")
        return ok and "NOT_FOUND" not in out

    def tar_extract(self, tar_path: str, dest: str) -> bool:
        """解压tar文件"""
        return self.run(f"tar -xf '{tar_path}' -C '{dest}' 2>/dev/null")[0]

    def zip_create(self, zip_path: str, src_dir: str) -> bool:
        """
        创建zip文件
        修复v3.0.0中cd&&zip在独立su -c子shell中失效的bug
        使用subshell分组: (cd path && zip ...)
        """
        return self.run(f"(cd '{src_dir}' && zip -r '{zip_path}' . 2>/dev/null)")[0]

    def pipe_run(self, commands: list) -> Tuple[bool, str, str]:
        """执行管道命令列表"""
        pipe_cmd = " | ".join(commands)
        return self.run(pipe_cmd)

    def file_browser(self, start_dir: str = "/sdcard", pattern: str = "*.img") -> List[str]:
        """
        文件浏览器 - 查找指定模式的文件，返回文件路径列表
        """
        results = []
        # 搜索常见位置的img文件
        search_dirs = [
            start_dir,
            "/sdcard/Download",
            "/sdcard/AndroidRootToolbox",
            "/data/local/tmp",
        ]
        for d in search_dirs:
            if self.dir_exists(d):
                ok, out, _ = self.run(
                    f"find '{d}' -maxdepth 3 -name '{pattern}' -type f 2>/dev/null | head -20"
                )
                if ok and out:
                    for line in out.strip().split("\n"):
                        line = line.strip()
                        if line and line not in results:
                            results.append(line)
        return results

    def file_browser_interactive(self, start_dir: str = "/sdcard", pattern: str = "*") -> Optional[str]:
        """
        交互式文件浏览器 - 列出目录内容并让用户选择
        返回选中的文件/目录路径，或None
        """
        import os as _os
        current_dir = start_dir
        while True:
            # 列出当前目录
            ok, out, _ = self.run(f"ls -1a '{current_dir}' 2>/dev/null")
            if not ok:
                return None
            
            items = out.strip().split("\n") if out.strip() else []
            # 过滤并分类
            dirs = []
            files = []
            for item in items:
                if item in [".", ".."]:
                    continue
                full_path = _os.path.join(current_dir, item)
                is_dir = self.dir_exists(full_path)
                if is_dir:
                    dirs.append(item)
                else:
                    files.append(item)
            
            dirs.sort()
            files.sort()
            
            print(f"\n  Current: {current_dir}")
            print(f"  Directories: {', '.join(dirs[:10])}")
            print(f"  Files: {', '.join(files[:10])}")
            print(f"\n  [cd DIR] change dir  [select FILE] select file  [..] go up  [q] quit")
            
            choice = input("  > ").strip()
            if choice == "q":
                return None
            elif choice == "..":
                current_dir = _os.path.dirname(current_dir) or "/"
            elif choice.startswith("cd "):
                target = choice[3:].strip()
                new_path = target if target.startswith("/") else _os.path.join(current_dir, target)
                if self.dir_exists(new_path):
                    current_dir = new_path
                else:
                    print(f"  Directory not found: {target}")
            else:
                full_path = choice if choice.startswith("/") else _os.path.join(current_dir, choice)
                if self.file_exists(full_path):
                    return full_path
                elif self.dir_exists(full_path):
                    current_dir = full_path
                else:
                    print(f"  Not found: {choice}")

    def write_file_multi(self, file_paths: dict) -> bool:
        """
        批量写入多个文件
        file_paths = {"/path/file1": "content1", "/path/file2": "content2"}
        返回全部成功标志
        """
        all_ok = True
        for path, content in file_paths.items():
            if not self.write_file(path, content):
                all_ok = False
        return all_ok


# 全局单例
shell = ShellExecutor()
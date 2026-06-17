#!/system/bin/sh
# ============================================================
# AndWreBox - 安卓扳手盒子 v1.0 通用启动器
# 兼容: Termux | Magisk Python3模块 | 任意Root终端
# ============================================================

# ── 颜色输出 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}  AndWreBox - 安卓扳手盒子 v1.0${NC}"
echo ""

# ── 检测运行环境 ──
IS_TERMUX=0
PYTHON_BIN=""

# 检测 Termux
if [ -d "/data/data/com.termux" ] || [ -n "$PREFIX" ]; then
    IS_TERMUX=1
    if [ -x "$PREFIX/bin/python3" ]; then
        PYTHON_BIN="$PREFIX/bin/python3"
    elif [ -x "$PREFIX/bin/python" ]; then
        PYTHON_BIN="$PREFIX/bin/python"
    fi
    echo -e "  ${GREEN}检测到 Termux 环境${NC}"
fi

# 检测 Magisk/KernelSU Python3 模块
# v2 结构: system/bin/ (挂载到 /system/bin/) + system/lib/ (挂载到 /system/lib/)
if [ -z "$PYTHON_BIN" ]; then
    if [ -x "/system/bin/python3" ]; then
        PYTHON_BIN="/system/bin/python3"
        echo -e "  ${GREEN}检测到系统 Python3 模块 (Magisk/KernelSU)${NC}"
    elif [ -x "/data/adb/modules/python3_system_env/system/bin/python3" ]; then
        PYTHON_BIN="/data/adb/modules/python3_system_env/system/bin/python3"
        export LD_LIBRARY_PATH="/data/adb/modules/python3_system_env/system/lib:${LD_LIBRARY_PATH}"
        echo -e "  ${GREEN}检测到 Python3 模块 (直读路径)${NC}"
    elif [ -x "/data/adb/modules_update/python3_system_env/system/bin/python3" ]; then
        PYTHON_BIN="/data/adb/modules_update/python3_system_env/system/bin/python3"
        export LD_LIBRARY_PATH="/data/adb/modules_update/python3_system_env/system/lib:${LD_LIBRARY_PATH}"
        echo -e "  ${GREEN}检测到 Python3 模块 (KernelSU 路径)${NC}"
    fi
fi

# 回退: 全局搜索 python3
if [ -z "$PYTHON_BIN" ]; then
    PYTHON_BIN=$(which python3 2>/dev/null)
    if [ -z "$PYTHON_BIN" ]; then
        PYTHON_BIN=$(which python 2>/dev/null)
    fi
fi

# ── 找不到 Python ──
if [ -z "$PYTHON_BIN" ]; then
    echo -e "  ${RED}错误: 未找到 Python3${NC}"
    echo ""
    echo "  请先安装 Python3 环境:"
    echo "  • Termux: pkg install python"
    echo "  • Magisk: 刷入 Python3_System_Env 模块"
    echo ""
    exit 1
fi

echo -e "  Python: ${PYTHON_BIN}"
echo ""

# ── 设置环境变量 ──
# PYTHONPATH: 模块预装依赖路径
if [ -d "/data/python3_env/site-packages" ]; then
    export PYTHONPATH="/data/python3_env/site-packages:${PYTHONPATH}"
fi

# 确保 256 色终端
export TERM="${TERM:-xterm-256color}"

# ── 获取脚本所在目录 ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 检查依赖 ──
echo "  检查依赖..."
DEPS_OK=$($PYTHON_BIN -c "
try:
    import rich
    print('OK')
except:
    # 尝试从模块路径导入
    import sys
    sys.path.insert(0, '/data/python3_env/site-packages')
    try:
        import rich
        print('OK')
    except:
        print('MISSING')
" 2>/dev/null)

if [ "$DEPS_OK" != "OK" ]; then
    echo -e "  ${RED}缺少依赖: rich${NC}"
    echo "  正在尝试安装..."
    if [ -x "/data/adb/modules/python3_system_env/system/bin/pip3" ]; then
        /data/adb/modules/python3_system_env/system/bin/pip3 install rich --target=/data/python3_env/site-packages --no-cache-dir 2>/dev/null
    elif command -v pip3 >/dev/null 2>&1; then
        pip3 install rich --target=/data/python3_env/site-packages --no-cache-dir 2>/dev/null
    elif [ "$IS_TERMUX" = "1" ]; then
        pkg install python-rich -y 2>/dev/null || pip install rich 2>/dev/null
    fi
fi

# ── 启动 AndWreBox ──
exec $PYTHON_BIN "$SCRIPT_DIR/main.py" "$@"
"""一键构建 FYADR 单文件 exe。

用法（在仓库根目录）：
    python packaging/build_exe.py

流程：
    1. 构建前端静态产物（app/dist）
    2. 准备构建用虚拟环境（.venv-build）并安装运行依赖 + PyInstaller
    3. 调用 PyInstaller 产出 dist-exe/FYADR.exe

产物不依赖目标机器上的 Python 或 Node，可直接分发。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
DIST_DIR = APP_DIR / "dist"
VENV = ROOT / ".venv-build"
OUTPUT_DIR = ROOT / "dist-exe"
EXE_NAME = "FYADR.exe"


def run(cmd: list[str], cwd: Path | None = None, shell: bool = False) -> None:
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd or ROOT), shell=shell)
    if result.returncode != 0:
        raise SystemExit(f"命令执行失败（退出码 {result.returncode}）：{' '.join(cmd)}")


def venv_python() -> Path:
    candidate = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return candidate


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def require(tool: str) -> None:
    if shutil.which(tool) is None:
        raise SystemExit(f"未找到 {tool}，请先安装并加入 PATH。")
    print(f"[ok] {tool}")


def build_frontend() -> None:
    require(npm_command())
    if not (APP_DIR / "node_modules").is_dir():
        run([npm_command(), "--prefix", "app", "ci"])
    run([npm_command(), "--prefix", "app", "run", "build"])
    if not (DIST_DIR / "index.html").is_file():
        raise SystemExit("前端构建未产出 app/dist/index.html。")
    print(f"[ok] 前端产物 {DIST_DIR}")


def build_venv() -> Path:
    python = venv_python()
    if not python.is_file():
        run([sys.executable, "-m", "venv", str(VENV)])
    run([str(python), "-m", "pip", "install", "--upgrade", "pip", "-q"])
    run([str(python), "-m", "pip", "install", "-q", "-r", "requirements.txt", "pyinstaller"])
    return python


def build_exe(python: Path) -> Path:
    run(
        [
            str(python),
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            "dist-exe",
            "--workpath",
            "build-temp",
            str(ROOT / "packaging" / "fyadr.spec"),
        ]
    )
    exe = OUTPUT_DIR / EXE_NAME
    if not exe.is_file():
        raise SystemExit(f"未生成 {exe}")
    return exe


def main() -> int:
    if os.name != "nt":
        print("提示：当前不是 Windows 环境，产物将是本平台可执行文件，无法给 Windows 用户使用。")

    build_frontend()
    python = build_venv()
    exe = build_exe(python)

    size_mb = exe.stat().st_size / (1024 * 1024)
    print("\n构建完成")
    print(f"  文件：{exe}")
    print(f"  体积：{size_mb:.1f} MB")
    print("  分发：把这一个 exe 发给对方，双击即用，无需安装 Python / Node。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

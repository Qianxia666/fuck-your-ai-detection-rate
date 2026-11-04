"""FYADR 单文件启动器。

同时支持两种运行方式：
  1. 源码运行：python packaging/launcher.py
  2. 冻结运行：PyInstaller 打出的 FYADR.exe

两者差异只在于两个根目录：
  * 资源根目录：冻结后资源被解包到 sys._MEIPASS，而 core_config / web_app
    在导入时用 Path(__file__) 推算仓库根目录，在 PYZ 里会算错，这里显式纠正。
  * 数据根目录：默认放在 exe 同级的 FYADR-data 里，做到拷走即走、
    配置和文档都不落在系统用户目录。
"""

from __future__ import annotations

import os
import shutil
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

APP_NAME = "FYADR"
DEFAULT_PORT = 8765
HOST = "127.0.0.1"
DATA_DIR_NAME = "FYADR-data"
LEGACY_APP_DIR_NAME = "FYADR"


def _tidy_streams() -> None:
    """输出被重定向到文件或管道时统一用 UTF-8，避免中文按 GBK 落盘后乱码。

    直接挂在控制台上时不动：Python 走宽字符 API，Windows 控制台本身就能正确显示。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def base_dir() -> Path:
    """资源根目录：冻结时为解包目录，否则为仓库根目录。"""
    bundle = getattr(sys, "_MEIPASS", "")
    if bundle:
        return Path(bundle)
    return Path(__file__).resolve().parents[1]


BASE = base_dir()
SCRIPTS_DIR = BASE / "scripts"
if SCRIPTS_DIR.is_dir() and str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def app_dir() -> Path:
    """程序所在目录：冻结时是 exe 所在目录，否则是仓库根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def legacy_config_dir() -> Path:
    """旧版本使用的系统用户目录，仅在迁移时读取。"""
    app_data = os.getenv("APPDATA", "").strip()
    if app_data:
        return Path(app_data) / LEGACY_APP_DIR_NAME
    return Path.home() / ".fyadr"


def migrate_legacy_config(target: Path) -> None:
    """首次切换到便携目录时，把旧 %APPDATA% 里的配置搬过来。

    只在目标目录还没有 config.json 时执行，拷贝而非移动，旧数据保持原样。
    """
    if (target / "config.json").is_file():
        return
    legacy = legacy_config_dir()
    if not (legacy / "config.json").is_file():
        return
    try:
        shutil.copytree(legacy, target, dirs_exist_ok=True)
        print(f"已从 {legacy} 迁移历史配置。", flush=True)
    except OSError as exc:
        print(f"历史配置迁移失败，将使用全新配置：{exc}", flush=True)


def configure_storage(force_appdata: bool = False) -> Path | None:
    """把配置与数据目录固定到 exe 同级，实现绿色便携。

    返回实际使用的便携目录；返回 None 表示沿用系统用户目录。
    显式的 FYADR_CONFIG_DIR 环境变量优先级最高，不会被覆盖。
    """
    if force_appdata:
        return None
    if os.getenv("FYADR_CONFIG_DIR", "").strip():
        return None

    target = app_dir() / DATA_DIR_NAME
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError:
        print(
            f"提示：{target} 不可写（可能是只读目录或缺少权限），"
            "改用系统用户目录存放配置。",
            flush=True,
        )
        return None

    migrate_legacy_config(target)
    os.environ["FYADR_CONFIG_DIR"] = str(target)
    return target


def resolve_port() -> int:
    raw = (os.getenv("FYADR_PORT") or "").strip()
    if not raw:
        return DEFAULT_PORT
    try:
        port = int(raw)
    except ValueError:
        return DEFAULT_PORT
    return port if 1 <= port <= 65535 else DEFAULT_PORT


def is_serving(port: int, timeout: float = 1.0) -> bool:
    """本地端口上是否已经有 FYADR 在响应。"""
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/api/ping", timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((HOST, port)) != 0


def open_browser_when_ready(url: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_serving(port, timeout=0.5):
            try:
                webbrowser.open(url)
            except Exception:
                pass
            return
        time.sleep(0.3)


def patch_frozen_paths() -> None:
    """纠正被冻结模块里按源码位置推算出来的路径常量。"""
    import core_config

    core_config.ROOT_DIR = BASE

    prompt_file = BASE / "prompts" / "defaults" / "classical-rewrite.md"
    try:
        content = prompt_file.read_text(encoding="utf-8").strip()
    except OSError:
        content = ""
    if content:
        # BUILTIN_TEMPLATES 持有同一个 dict 引用，default_config() 在 load_config()
        # 时才 deepcopy，所以此处就地改写在首次生成配置时生效。
        core_config.BUILTIN_TEMPLATE["content"] = content


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    want_browser = "--no-browser" not in args
    force_appdata = "--appdata" in args
    port = resolve_port()
    url = f"http://{HOST}:{port}"

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    _tidy_streams()

    if is_serving(port):
        print(f"{APP_NAME} 已在运行，直接打开 {url}", flush=True)
        if want_browser:
            webbrowser.open(url)
        return 0

    if not port_available(port):
        print(
            f"端口 {port} 被其他程序占用。可设置环境变量 FYADR_PORT 换个端口后重试。",
            flush=True,
        )
        return 1

    storage_dir = configure_storage(force_appdata=force_appdata)
    patch_frozen_paths()

    import web_app

    web_app.FRONTEND_DIST = BASE / "app" / "dist"
    if not (web_app.FRONTEND_DIST / "index.html").is_file():
        print("缺少前端构建产物 app/dist，无法提供界面。请先运行 build_exe.bat。", flush=True)
        return 1

    import core_config
    from werkzeug.serving import make_server

    config = core_config.load_config()
    config_dir = storage_dir or core_config.get_config_dir()
    mode = "便携模式" if storage_dir else "系统用户目录"

    try:
        server = make_server(HOST, port, web_app.app, threaded=True)
    except OSError as exc:
        print(f"启动失败：{exc}", flush=True)
        return 1

    print("=" * 60)
    print(f"  {APP_NAME} 已启动：{url}")
    print(f"  数据目录（{mode}）：{config_dir}")
    print(f"  已配置模型连接：{len(config.get('modelProfiles', []))} 个")
    print("  关闭本窗口即停止服务。")
    print("=" * 60, flush=True)

    if want_browser:
        threading.Thread(
            target=open_browser_when_ready, args=(url, port), daemon=True
        ).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在退出 …")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

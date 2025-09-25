import os
import subprocess
import sys
import time
import socket
import getpass

# 默认配置（可在 scripts/mysql_local.py 中覆盖）
CONFIG_DEFAULTS = {
    # MySQL 启动方式（二选一）：优先使用服务名，其次使用 mysqld.exe 路径
    'MYSQL_SERVICE': None,  # 例如 'MySQL80'；若未注册服务请保持为 None
    'MYSQLD_EXE': 'D:/mysql/mysql-8.0.19-winx64/bin/mysqld.exe',
    'MYSQL_DEFAULTS_FILE': 'D:/mysql/mysql-8.0.19-winx64/my.ini',

    # Django 连接参数
    'MYSQL_HOST': '127.0.0.1',
    'MYSQL_PORT': '3306',
    'MYSQL_DATABASE': 'warehouse_db',
    'MYSQL_USER': 'root',
    'MYSQL_PASSWORD': '',  # 若有密码，建议在 scripts/mysql_local.py 中设置
}


def load_config():
    cfg = CONFIG_DEFAULTS.copy()
    # 尝试用本地配置覆盖（不纳入版本控制）
    try:
        from scripts.mysql_local import CONFIG as LOCAL_CONFIG  # type: ignore
        if isinstance(LOCAL_CONFIG, dict):
            cfg.update({k: v for k, v in LOCAL_CONFIG.items() if v is not None})
    except Exception:
        pass
    # 环境变量再次覆盖（如果有）
    for key in list(cfg.keys()):
        env_v = os.environ.get(key)
        if env_v is not None:
            cfg[key] = env_v
    return cfg


def _print(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def wait_for_mysql_ready(timeout: int = 30) -> bool:
    cfg = load_config()
    host = cfg.get('MYSQL_HOST', '127.0.0.1')
    port = int(str(cfg.get('MYSQL_PORT', '3306')))
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                _print("[ok] MySQL 端口已监听")
                return True
        except OSError as e:
            _print(f"[wait] 等待 MySQL 端口 {host}:{port} … {e}")
            time.sleep(1.0)
    _print("[error] 等待 MySQL 启动超时")
    return False


def start_mysql():
    cfg = load_config()
    service = cfg.get('MYSQL_SERVICE')  # 例如 MySQL80
    mysqld = cfg.get('MYSQLD_EXE')  # 例如 D:\\mysql\\mysql-8.0.19-winx64\\bin\\mysqld.exe
    defaults = cfg.get('MYSQL_DEFAULTS_FILE')  # 例如 D:\\mysql\\mysql-8.0.19-winx64\\my.ini

    if service:
        _print(f"[info] 尝试启动 MySQL 服务: {service}")
        try:
            subprocess.check_call(["net", "start", str(service)], shell=True)
            return {"mode": "service", "service": service, "proc": None}
        except subprocess.CalledProcessError as e:
            _print(f"[warn] 启动服务失败: {e}. 将尝试 mysqld 方式…")

    if mysqld:
        cmd = [str(mysqld)]
        if defaults:
            cmd.append(f"--defaults-file={defaults}")
        _print(f"[info] 启动 mysqld: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd)
        return {"mode": "process", "proc": proc}

    raise SystemExit(
        "未配置 MYSQL_SERVICE 或 MYSQLD_EXE，无法自动启动 MySQL。\n"
        "请设置环境变量：MYSQL_SERVICE=MySQL80 或 MYSQLD_EXE=mysqld.exe 全路径。"
    )


def stop_mysql(ctx):
    mode = ctx.get("mode")
    if mode == "service":
        service = ctx.get("service")
        if service:
            _print(f"[info] 停止 MySQL 服务: {service}")
            try:
                subprocess.check_call(["net", "stop", service], shell=True)
            except subprocess.CalledProcessError as e:
                _print(f"[warn] 停止服务失败: {e}")
    elif mode == "process":
        proc: subprocess.Popen | None = ctx.get("proc")
        if proc and proc.poll() is None:
            _print("[info] 终止 mysqld 进程…")
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    _print("[warn] 强制结束 mysqld 进程…")
                    proc.kill()
            except Exception as e:
                _print(f"[warn] 结束 mysqld 失败: {e}")


def run_django() -> int:
    # 将配置写入当前进程的环境变量，让 Django settings 读取
    cfg = load_config()
    # 如未提供密码，交互式输入（避免把密码写入文件/环境变量）
    if not cfg.get('MYSQL_PASSWORD'):
        try:
            pwd = getpass.getpass('[input] 请输入 MySQL 密码（root）：')
            cfg['MYSQL_PASSWORD'] = pwd or ''
        except Exception:
            pass
    for key in (
        'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DATABASE', 'MYSQL_USER', 'MYSQL_PASSWORD'
    ):
        os.environ[key] = str(cfg.get(key, '') or '')

    cmd = [sys.executable, "manage.py", "runserver"]
    _print(f"[info] 运行: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main() -> None:
    ctx = start_mysql()
    try:
        if not wait_for_mysql_ready(timeout=30):
            raise SystemExit(1)
        code = run_django()
        sys.exit(code)
    except KeyboardInterrupt:
        _print("[info] 收到中断，准备退出…")
    finally:
        stop_mysql(ctx)


if __name__ == "__main__":
    main()

import os
import sys
import atexit
import socket


def _is_port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _maybe_autostart_mysql(cmd: str):
    if os.environ.get('DISABLE_AUTO_MYSQL'):
        return
    # 避免与自带 devserver 命令重复，以及 runserver 子进程重复启动
    if cmd in ('devserver',):
        return
    if cmd == 'runserver' and os.environ.get('RUN_MAIN') == 'true':
        return
    try:
        from scripts.runserver_with_mysql import load_config, start_mysql, wait_for_mysql_ready, stop_mysql
    except Exception:
        return

    cfg = load_config()
    host = str(cfg.get('MYSQL_HOST', '127.0.0.1'))
    try:
        port = int(str(cfg.get('MYSQL_PORT', '3306')))
    except Exception:
        port = 3306

    if _is_port_open(host, port):
        return

    # 启动并在退出时关闭
    try:
        ctx = start_mysql()
    except SystemExit:
        return
    except Exception:
        return

    def _cleanup():
        try:
            stop_mysql(ctx)
        except Exception:
            pass

    atexit.register(_cleanup)
    wait_for_mysql_ready(timeout=30)


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable?"
        ) from exc

    # 注入 MySQL 连接环境变量（从 scripts/mysql_local.py 或默认配置读取）
    try:
        from scripts.runserver_with_mysql import load_config  # type: ignore
        cfg = load_config()
        for key in ('MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DATABASE', 'MYSQL_USER', 'MYSQL_PASSWORD'):
            val = cfg.get(key)
            if val is not None:
                os.environ[key] = str(val)
    except Exception:
        pass

    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    _maybe_autostart_mysql(cmd)
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

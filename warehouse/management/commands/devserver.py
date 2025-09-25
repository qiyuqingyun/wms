import os
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "自动启动 MySQL 后再启动 Django 开发服务器（退出时自动关闭 MySQL）"

    def add_arguments(self, parser):
        parser.add_argument('addrport', nargs='?', default='127.0.0.1:8000', help='地址与端口，默认 127.0.0.1:8000')
        parser.add_argument('--noreload', action='store_true', help='关闭自动重载')
        parser.add_argument('--insecure', action='store_true', help='允许直接提供静态文件（DEBUG 用）')

    def handle(self, *args, **options):
        # 复用脚本中的启动/等待/关闭/配置注入逻辑
        try:
            from scripts.runserver_with_mysql import (
                start_mysql,
                wait_for_mysql_ready,
                stop_mysql,
                load_config,
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"无法导入脚本: {e}. 请确认 scripts/runserver_with_mysql.py 存在。"))
            return

        # 将配置注入到环境变量，确保 Django settings 能读取到（含密码）
        cfg = load_config()
        for key in ('MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DATABASE', 'MYSQL_USER', 'MYSQL_PASSWORD'):
            if cfg.get(key) is not None:
                os.environ[key] = str(cfg.get(key))

        is_child = os.environ.get('RUN_MAIN') == 'true'
        ctx = None
        try:
            if not is_child:
                ctx = start_mysql()
                if not wait_for_mysql_ready(timeout=30):
                    self.stderr.write(self.style.ERROR('等待 MySQL 启动超时'))
                    return
            addrport = options['addrport']
            use_reloader = not options['noreload']
            insecure = options['insecure']
            if not is_child:
                self.stdout.write(self.style.SUCCESS('MySQL 就绪，启动 Django…'))
            call_command('runserver', addrport, use_reloader=use_reloader, insecure=insecure)
        finally:
            if ctx is not None:
                stop_mysql(ctx)

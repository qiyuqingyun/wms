# 本地 MySQL 启动与连接参数（可选）。
# 使用方式：复制为 scripts/mysql_local.py 并按需修改；该文件可包含你的本地密码，不建议提交到仓库。

CONFIG = {
    # 启动方式：若你注册了服务，给出服务名；否则留空并配置 mysqld 路径
    'MYSQL_SERVICE': None,            # 例如 'MySQL80'
    'MYSQLD_EXE': '',
    'MYSQL_DEFAULTS_FILE': '',

    # Django 连接参数
    'MYSQL_HOST': '127.0.0.1',
    'MYSQL_PORT': '3306',
    'MYSQL_DATABASE': '',
    'MYSQL_USER': 'root',
    'MYSQL_PASSWORD': '',            # 在此填写你的本地密码（如有）
}

仓库管理系统（Django + MySQL）
===========================

功能概览
--------
- 管理员：通过 Django Admin 维护商品详情、物品分类、用户与权限。
- 一般用户（Operators）：维护商品包装/分类信息、执行入库/出库、查看库存及临期信息。
- 数据表：
  - 物品分类（Category）定义分类、排序与简介
  - 物品详情（Item）含名称、SKU、规格、体积、是否保质期、图片等
  - 仓储位置（Location）含容量体积，自动计算已用/可用
  - 批次（ItemBatch）含批次号、生产/过期日期、批次条码、数量
  - 批次-货位分配（BatchLocation）解决单批次多货位
  - 出入明细（Movement）记录入/出库流水、数量、时间、用户、货位
- 前端能力：
  - 分类轮播：每个分类内的商品以滑动/滚轮/拖拽方式浏览，聚焦商品自动放大
  - 商品详情轮播：商品图片支持左右翻页、聚焦放大显示
  - 库存总览：按商品汇总批次数、总库存、临期数量与货位分布
  - 包装维护：支持按分类/关键词筛选，并快速编辑包装规格、体积等字段
  - 高频进出与临期批次页面用于运营决策
- 扫码入库/出库：输入数字识别码（SKU 或批次条码）调出详情，按批次调整数量并记录时间。
- 货位容量检查：优先货位不足时，系统自动分配到其他有剩余空间的货位。
- 权限模型：
  - Managers：拥有应用内所有模型的增删改查权限
  - Operators：可查看 Item/ItemBatch/Location/BatchLocation，新增 Movement，并可修改 Item 包装信息


目录结构
--------
- `mywebsite/`：项目配置、数据库/静态资源设置
- `warehouse/`：业务应用（models、views、urls、admin、forms、signals）
- `templates/`：页面模板（包含轮播组件、分类页、库存页等）
- `static/`：样式与轮播脚本
- `scripts/`：开发辅助脚本（可选 MySQL 自动启动）

环境准备
--------
1. 创建并激活 Python 环境，安装依赖（`pip install -r requirements.txt`）。
2. 准备 MySQL 数据库并写入环境变量：
  ```txt
     在scripts文件夹下新建mysql_local.py文件，并把mysql_example_local.py的内容复制过来。
     安装mysql数据库，配置其.ini文件，然后创建warehouse_db数据库。
     在mysql_local.py文件中，正确配置数据库连接信息。
  ```
初始化与运行（按顺序执行）
------------
1. 迁移数据：
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```
2. 创建超级用户：
   ```powershell
   python manage.py createsuperuser
   ```
3. 启动服务：
   ```powershell
   python manage.py runserver
   ```
4. 常用入口：
   - `/` 仪表盘
   - `/catalog/` 分类轮播
   - `/scan/` 扫码/查询
   - `/inbound/` 入库
   - `/outbound/` 出库
   - `/inventory/` 库存总览（含临期批次）
   - `/near-expiry/` 临期列表
   - `/popular/` 高频进出
   - `/locations/` 货位管理
   - `/packaging/` 包装维护

使用要点
--------
- 物品图片：通过 Admin 在商品中添加图片，前台自动展示轮播特效。
- 扫码入/出库：
  - `/scan/` 输入 SKU 或批次条码调出商品/批次信息
  - 支持跳转到入库页面并预填批次信息
- 包装维护：Operators 组拥有 Item 修改权限，可在“包装维护”页批量更新包装规格、体积、保质期标记等。
- 库存总览：展示总库存、临期数量以及货位分布，方便运营统筹。
- 货位容量：优先货位空间不足时，系统会自动按照剩余容量依次分配至其他货位。

# Generated manually to add categories and packaging maintenance support

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='名称')),
                ('slug', models.SlugField(help_text='用于URL或筛选的唯一标识', max_length=120, unique=True, verbose_name='别名')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('order', models.PositiveIntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
            ],
            options={
                'ordering': ('order', 'name'),
                'verbose_name': '物品分类',
                'verbose_name_plural': '物品分类',
            },
        ),
        migrations.AddField(
            model_name='item',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items',
                to='warehouse.category',
                verbose_name='分类',
            ),
        ),
        migrations.AlterModelOptions(
            name='batchlocation',
            options={'verbose_name': '批次货位', 'verbose_name_plural': '批次货位'},
        ),
        migrations.AlterModelOptions(
            name='item',
            options={'ordering': ('name',), 'verbose_name': '商品', 'verbose_name_plural': '商品'},
        ),
        migrations.AlterModelOptions(
            name='itembatch',
            options={'ordering': ('item__name', 'batch_number'), 'verbose_name': '商品批次', 'verbose_name_plural': '商品批次'},
        ),
        migrations.AlterModelOptions(
            name='itemimage',
            options={'verbose_name': '商品图片', 'verbose_name_plural': '商品图片'},
        ),
        migrations.AlterModelOptions(
            name='location',
            options={'ordering': ('code',), 'verbose_name': '仓储位置', 'verbose_name_plural': '仓储位置'},
        ),
        migrations.AlterModelOptions(
            name='movement',
            options={'ordering': ('-created_at',), 'verbose_name': '出入库明细', 'verbose_name_plural': '出入库明细'},
        ),
    ]

#!/usr/bin/env python
"""
简单测试脚本来验证我们的重复行修复是否正确工作
"""
import tablib
from django.test import TestCase
from django.conf import settings
import django

# 配置最小化的 Django 设置
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ]
    )
    django.setup()

# 导入我们需要的模块
from import_export import resources, fields
from django.db import models


# 创建一个简单的测试模型
class Book(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    author_email = models.EmailField(null=True, blank=True)
    
    class Meta:
        app_label = 'testapp'


# 创建我们的资源类
class BookResource(resources.ModelResource):
    class Meta:
        model = Book
        import_id_fields = ('id',)
        use_bulk = True


class TestDuplicateRows(TestCase):
    def setUp(self):
        # 创建数据库表
        from django.db import connection
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Book)
    
    def test_duplicate_rows_in_import(self):
        """测试包含重复行的数据集在导入时应该更新而不是重复创建"""
        # 创建包含重复行的数据集
        dataset = tablib.Dataset(headers=["id", "name", "author_email"])
        # 同一个 ID 出现多次，每次有不同的名称
        dataset.append([1, "First Name", "first@example.com"])
        dataset.append([1, "Second Name", "second@example.com"])  # 重复行！
        dataset.append([1, "Final Name", "final@example.com"])     # 又一个重复行！
        dataset.append([2, "Another Book", "another@example.com"])
        
        resource = BookResource()
        result = resource.import_data(dataset, raise_errors=True, dry_run=False)
        
        # 验证只有 2 本书被创建（ID 1 和 2），而不是 4 本
        self.assertEqual(Book.objects.count(), 2)
        
        # 验证第一本书被更新到了最后的名称
        book1 = Book.objects.get(id=1)
        self.assertEqual(book1.name, "Final Name")
        self.assertEqual(book1.author_email, "final@example.com")
        
        # 验证导入结果：应该有 1 个新实例（ID 2）和 2 个更新（ID 1 有两次更新）
        print(f"Total rows: {result.total_rows}")
        print(f"New: {result.totals.get('new', 0)}, Update: {result.totals.get('update', 0)}")
        
        # 总共应该处理 4 行，但只有 2 个实际对象
        self.assertEqual(result.total_rows, 4)


if __name__ == "__main__":
    # 运行测试
    from django.test import run_tests
    import sys
    failures = run_tests([__name__], verbosity=2)
    sys.exit(failures)

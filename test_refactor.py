#!/usr/bin/env python
"""
测试重构后的 fields.py 是否保持向后兼容并消除重复转换
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from import_export.fields import Field
from import_export.widgets import Widget

# 创建一个测试 Widget，用于跟踪 clean 方法被调用的次数
class TestWidget(Widget):
    def __init__(self):
        super().__init__()
        self.clean_called_count = 0
    
    def clean(self, value, row=None, *args, **kwargs):
        self.clean_called_count += 1
        # 进行一个简单的转换
        if isinstance(value, str):
            return value.upper()
        return value

# 创建一个简单的测试类来模拟 Django 模型
class TestInstance:
    def __init__(self):
        self.test_field = None

# 测试向后兼容性
def test_backward_compatibility():
    print("测试向后兼容性...")
    widget = TestWidget()
    field = Field(attribute='test_field', column_name='test_col', widget=widget)
    instance = TestInstance()
    
    # 使用旧的 API：只传递 row
    row = {'test_col': 'hello'}
    field.save(instance, row)
    
    # 验证结果
    assert instance.test_field == 'HELLO', "值没有被正确转换"
    assert widget.clean_called_count == 1, "clean 方法应该只被调用一次（向后兼容模式）"
    
    print("✓ 向后兼容性测试通过！")

# 测试新功能：传递已清理的值
def test_new_feature():
    print("\n测试新功能：传递已清理的值...")
    widget = TestWidget()
    field = Field(attribute='test_field', column_name='test_col', widget=widget)
    instance = TestInstance()
    
    # 先 clean 一次
    row = {'test_col': 'world'}
    cleaned_value = field.clean(row)
    
    # 然后用 cleaned_value 直接保存
    field.save(instance, cleaned=cleaned_value)
    
    # 验证结果
    assert instance.test_field == 'WORLD', "值没有被正确设置"
    assert widget.clean_called_count == 1, "clean 方法应该只被调用一次（使用新功能）"
    
    print("✓ 新功能测试通过！")

# 运行所有测试
if __name__ == "__main__":
    test_backward_compatibility()
    test_new_feature()
    print("\n🎉 所有测试通过！")

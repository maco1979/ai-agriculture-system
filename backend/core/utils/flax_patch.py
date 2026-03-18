"""
Flax兼容性补丁
用于修复Flax与Python 3.14的兼容性问题
"""

import dataclasses


def apply_flax_patch():
    """应用Flax兼容性补丁"""
    print("正在应用Flax兼容性补丁...")
    
    # 保存原始的_process_class函数
    original_process_class = dataclasses._process_class
    
    def patched_process_class(cls, init, repr, eq, order, unsafe_hash, frozen, match_args, kw_only, slots, weakref_slot):
        """修补dataclasses._process_class，允许没有类型注释的字段"""
        try:
            return original_process_class(cls, init, repr, eq, order, unsafe_hash, frozen, match_args, kw_only, slots, weakref_slot)
        except TypeError as e:
            if "is a field but has no type annotation" in str(e):
                # 获取类的所有字段
                fields = []
                for name, value in cls.__dict__.items():
                    if isinstance(value, dataclasses.Field):
                        fields.append(name)
                
                # 为没有类型注释的字段添加类型注释
                if not hasattr(cls, '__annotations__'):
                    cls.__annotations__ = {}
                
                for field_name in fields:
                    if field_name not in cls.__annotations__:
                        cls.__annotations__[field_name] = type(None)
                
                # 再次尝试处理类
                return original_process_class(cls, init, repr, eq, order, unsafe_hash, frozen, match_args, kw_only, slots, weakref_slot)
            raise
    
    # 应用补丁
    dataclasses._process_class = patched_process_class
    print("已应用dataclasses兼容性补丁")
    print("Flax兼容性补丁已应用")

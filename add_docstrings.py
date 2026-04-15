#!/usr/bin/env python3
"""
扫描 src 目录下的 Python 文件，为缺少 docstring 的函数、类和方法添加基本 docstring。
"""

import ast
import os
import sys
from pathlib import Path

def has_docstring(node):
    """检查 AST 节点是否有 docstring。"""
    if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
        return False
    if node.body and isinstance(node.body[0], ast.Expr):
        if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            return True
        # Python 3.7 及以下版本可能使用 ast.Str
        if hasattr(ast, 'Str') and isinstance(node.body[0].value, ast.Str):
            return True
    return False

def generate_docstring(node, class_name=None):
    """为节点生成基本 docstring。"""
    if isinstance(node, ast.ClassDef):
        return f'"""{node.name} 类。"""'
    
    # 函数或方法
    func_name = node.name
    if class_name:
        desc = f'{func_name} 方法'
    else:
        desc = f'{func_name} 函数'
    
    # 简单描述
    return f'"""{desc}。"""'

def add_docstrings_to_file(filepath):
    """为文件中的节点添加缺失的 docstring。"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"无法读取文件 {filepath}，跳过")
        return None
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"语法错误 {filepath}: {e}，跳过")
        return None
    
    changes = []
    
    # 遍历所有节点
    for node in ast.walk(tree):
        # 只处理函数、异步函数和类定义
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            if not has_docstring(node):
                # 确定类名（如果是方法）
                class_name = None
                parent = node
                while hasattr(parent, 'parent'):
                    parent = parent.parent
                    if isinstance(parent, ast.ClassDef):
                        class_name = parent.name
                        break
                
                # 生成 docstring
                docstring = generate_docstring(node, class_name)
                
                # 创建 docstring 节点
                if sys.version_info >= (3, 8):
                    doc_node = ast.Expr(value=ast.Constant(value=docstring, kind=None))
                else:
                    # Python 3.7 及以下
                    doc_node = ast.Expr(value=ast.Str(s=docstring))
                
                # 插入到 body 的开头
                node.body.insert(0, doc_node)
                changes.append((node.name, docstring))
    
    if changes:
        # 将修改后的 AST 转换回代码
        try:
            new_content = ast.unparse(tree) if hasattr(ast, 'unparse') else None
            if new_content is None:
                # 如果没有 ast.unparse，我们需要手动应用更改
                # 这里简化为输出报告
                print(f"需要为 {filepath} 添加 docstring 的节点：")
                for name, doc in changes:
                    print(f"  - {name}: {doc}")
                return None
            return new_content
        except Exception as e:
            print(f"无法生成代码 {filepath}: {e}")
            return None
    
    return None

def main():
    src_dir = Path(__file__).parent / "src"
    if not src_dir.exists():
        print("src 目录不存在")
        return
    
    # 收集所有 .py 文件
    py_files = list(src_dir.rglob("*.py"))
    print(f"找到 {len(py_files)} 个 Python 文件")
    
    # 跳过测试文件
    py_files = [f for f in py_files if "test" not in str(f).lower()]
    print(f"过滤后剩余 {len(py_files)} 个文件")
    
    for filepath in py_files:
        print(f"处理 {filepath.relative_to(src_dir)}...")
        new_content = add_docstrings_to_file(filepath)
        if new_content:
            # 备份原文件
            backup = filepath.with_suffix(filepath.suffix + ".bak")
            try:
                import shutil
                shutil.copy2(filepath, backup)
                print(f"  已备份到 {backup.name}")
            except Exception as e:
                print(f"  备份失败: {e}")
                continue
            
            # 写入新内容
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"  已更新")
            except Exception as e:
                print(f"  写入失败: {e}")
                # 恢复备份
                try:
                    shutil.copy2(backup, filepath)
                except:
                    pass
        else:
            print(f"  无需更新")

if __name__ == "__main__":
    main()
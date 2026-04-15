#!/usr/bin/env python3
"""
扫描 src 目录下的 Python 文件，为缺少 docstring 的函数、类和方法添加基本 docstring。
通过文本插入实现，保持原有格式。
"""

import ast
import os
import sys
from pathlib import Path

def has_docstring(node):
    """检查 AST 节点是否有 docstring。"""
    if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
        return False
    if node.body:
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                return True
        # 处理 Python 3.7 及以下的 ast.Str
        if hasattr(ast, 'Str') and isinstance(first, ast.Expr) and isinstance(first.value, ast.Str):
            return True
    return False

def get_node_location(node):
    """返回节点的起始行号、结束行号以及缩进级别。"""
    # 尝试从节点获取行号
    start_line = node.lineno if hasattr(node, 'lineno') else None
    # 对于函数/类，结束行号可能通过 decorator_list 或 body 计算
    # 这里简化：使用起始行号
    return start_line

def add_docstrings_to_file(filepath):
    """为文件中的节点添加缺失的 docstring。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    try:
        tree = ast.parse(''.join(lines))
    except SyntaxError as e:
        print(f"语法错误 {filepath}: {e}，跳过")
        return None, 0
    
    # 收集需要添加 docstring 的节点及其信息
    nodes_to_add = []
    
    # 为每个节点添加 parent 引用
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            if not has_docstring(node):
                # 确定缩进级别
                # 找到节点定义的行
                line_no = node.lineno - 1  # 转换为0索引
                if line_no < 0 or line_no >= len(lines):
                    continue
                
                line = lines[line_no]
                # 计算前导空格
                indent = len(line) - len(line.lstrip())
                
                # 确定节点类型
                if isinstance(node, ast.ClassDef):
                    docstring = f'{" " * indent}"""{node.name} 类。"""'
                else:
                    # 函数或方法
                    # 检查是否是方法
                    is_method = hasattr(node, 'parent') and isinstance(node.parent, ast.ClassDef)
                    if is_method:
                        docstring = f'{" " * indent}"""{node.name} 方法。"""'
                    else:
                        docstring = f'{" " * indent}"""{node.name} 函数。"""'
                
                # 找到插入位置（函数/类定义后的第一行）
                # 如果函数体为空，可能只有一行
                if not node.body:
                    # 空体，在冒号后添加
                    insert_line = line_no + 1
                else:
                    # 有函数体，在第一个语句前插入
                    insert_line = node.body[0].lineno - 1
                
                nodes_to_add.append((insert_line, docstring))
    
    # 按行号降序排序，以便从后往前插入，避免行号变化
    nodes_to_add.sort(key=lambda x: x[0], reverse=True)
    
    # 应用插入
    for insert_line, docstring in nodes_to_add:
        lines.insert(insert_line, docstring + '\n')
    
    if nodes_to_add:
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return filepath, len(nodes_to_add)
    else:
        return None, 0

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
    
    total_added = 0
    for filepath in py_files:
        print(f"处理 {filepath.relative_to(src_dir)}...")
        result, count = add_docstrings_to_file(filepath)
        if result:
            print(f"  添加了 {count} 个 docstring")
            total_added += count
        else:
            print(f"  无需更新")
    
    print(f"\n总计添加了 {total_added} 个 docstring")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""修复 docstring 的缩进错误。"""

import re
from pathlib import Path

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    changes = []
    while i < len(lines):
        line = lines[i]
        # 检查是否是函数定义
        if re.match(r'^\s*def \w+\(', line) or re.match(r'^\s*class \w+', line):
            # 找到函数/类定义的缩进
            indent = len(line) - len(line.lstrip())
            # 默认缩进：增加 4 个空格
            expected_indent = indent + 4
            
            # 检查下一行是否是 docstring
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # docstring 可能以 """ 或 ''' 开头
                if re.match(r'^\s*""".*"""\s*$', next_line) or re.match(r"^\s*'''.*'''\s*$", next_line):
                    # 检查缩进
                    actual_indent = len(next_line) - len(next_line.lstrip())
                    if actual_indent != expected_indent:
                        # 修复缩进
                        new_line = ' ' * expected_indent + next_line.lstrip()
                        lines[i + 1] = new_line
                        changes.append((i + 1, actual_indent, expected_indent))
        i += 1
    
    if changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return len(changes)
    return 0

def main():
    src_dir = Path(__file__).parent / "src"
    
    # 收集所有 .py 文件
    py_files = list(src_dir.rglob("*.py"))
    print(f"找到 {len(py_files)} 个 Python 文件")
    
    # 跳过测试文件
    py_files = [f for f in py_files if "test" not in str(f).lower()]
    print(f"过滤后剩余 {len(py_files)} 个文件")
    
    total_fixed = 0
    for filepath in py_files:
        print(f"检查 {filepath.relative_to(src_dir)}...")
        fixed = fix_file(filepath)
        if fixed:
            print(f"  修复了 {fixed} 个缩进错误")
            total_fixed += fixed
    
    print(f"\n总计修复了 {total_fixed} 个缩进错误")

if __name__ == "__main__":
    main()
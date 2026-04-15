#!/usr/bin/env python3
"""恢复备份文件（.bak）到原始文件。"""

import os
import shutil
from pathlib import Path

def main():
    src_dir = Path(__file__).parent / "src"
    
    # 查找所有 .bak 文件
    bak_files = list(src_dir.rglob("*.bak"))
    print(f"找到 {len(bak_files)} 个备份文件")
    
    for bak_file in bak_files:
        original_file = bak_file.with_suffix('')  # 移除 .bak 后缀
        if original_file.exists():
            shutil.copy2(bak_file, original_file)
            print(f"已恢复 {original_file.relative_to(src_dir)}")
            # 可选：删除备份文件
            # bak_file.unlink()
        else:
            print(f"原始文件不存在: {original_file}")
    
    # 删除备份文件
    for bak_file in bak_files:
        bak_file.unlink()
    print(f"已删除所有备份文件")

if __name__ == "__main__":
    main()
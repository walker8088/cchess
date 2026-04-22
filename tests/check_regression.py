# -*- coding: utf-8 -*-
"""
性能回归检测脚本

对比当前性能与基线性能，检测性能回归。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 直接导入 benchmark 模块
import benchmark
from benchmark import run_all_benchmarks, BenchmarkResult


# 性能基线（允许 10% 的波动）
BASELINE = {
    "get_pieces": 0.030,      # ms
    "create_moves": 0.150,    # ms
    "is_valid_move": 0.005,   # ms
    "fench_to_species": 0.001, # ms
    "Rook moves": 0.050,      # ms
    "Cannon moves": 0.035,    # ms
    "Knight moves": 0.035,    # ms
    "Pawn moves": 0.035,      # ms
    "move_text": 0.005,       # ms
    "normalized": 0.060,      # ms
}

REGRESSION_THRESHOLD = 0.10  # 10% 回归阈值


def check_regression(results: List[BenchmarkResult]) -> Dict:
    """检查性能回归。
    
    参数:
        results: 基准测试结果列表
    
    返回:
        包含回归信息的字典
    """
    regressions = []
    improvements = []
    
    for result in results:
        if result.name in BASELINE:
            baseline_time = BASELINE[result.name]
            current_time = result.avg_time_ms
            change = (current_time - baseline_time) / baseline_time
            
            if change > REGRESSION_THRESHOLD:
                regressions.append({
                    "name": result.name,
                    "baseline_ms": baseline_time,
                    "current_ms": current_time,
                    "change_pct": change * 100,
                })
            elif change < -REGRESSION_THRESHOLD:
                improvements.append({
                    "name": result.name,
                    "baseline_ms": baseline_time,
                    "current_ms": current_time,
                    "change_pct": change * 100,
                })
    
    return {
        "regressions": regressions,
        "improvements": improvements,
        "total_tests": len(results),
        "passed": len(results) - len(regressions),
    }


def save_baseline(results: List[BenchmarkResult], filepath: str = "baseline.json"):
    """保存性能基线到文件。
    
    参数:
        results: 基准测试结果列表
        filepath: 输出文件路径
    """
    baseline = {}
    for result in results:
        baseline[result.name] = result.avg_time_ms
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    
    print(f"\n性能基线已保存到: {filepath}")


def load_baseline(filepath: str = "baseline.json") -> Dict:
    """从文件加载性能基线。
    
    参数:
        filepath: 输入文件路径
    
    返回:
        性能基线字典
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def main():
    """主函数"""
    print("="*60)
    print("CChess 性能回归检测")
    print("="*60)
    
    # 运行基准测试
    results = run_all_benchmarks()
    
    # 检查回归
    report = check_regression(results)
    
    # 打印报告
    print(f"\n{'='*60}")
    print("回归检测报告")
    print(f"{'='*60}")
    print(f"总测试数: {report['total_tests']}")
    print(f"通过: {report['passed']}")
    print(f"回归: {len(report['regressions'])}")
    print(f"改进: {len(report['improvements'])}")
    
    if report["regressions"]:
        print(f"\n{'='*60}")
        print("性能回归 (超过 10% 阈值)")
        print(f"{'='*60}")
        for reg in report["regressions"]:
            print(f"  {reg['name']}: {reg['baseline_ms']:.3f} ms -> {reg['current_ms']:.3f} ms ({reg['change_pct']:+.1f}%)")
    
    if report["improvements"]:
        print(f"\n{'='*60}")
        print("性能改进")
        print(f"{'='*60}")
        for imp in report["improvements"]:
            print(f"  {imp['name']}: {imp['baseline_ms']:.3f} ms -> {imp['current_ms']:.3f} ms ({imp['change_pct']:+.1f}%)")
    
    # 保存基线
    save_baseline(results)
    
    # 返回状态码
    if report["regressions"]:
        print("\n[WARNING] 检测到性能回归！")
        return 1
    else:
        print("\n[PASS] 无性能回归")
        return 0


if __name__ == "__main__":
    sys.exit(main())

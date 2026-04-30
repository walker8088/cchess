#!/usr/bin/env python3
"""
覆盖率分析脚本 - 分析测试用例的覆盖数据并检查未覆盖的代码
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class CoverageAnalyzer:
    """覆盖率分析器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.coverage_data: Dict[str, Dict] = {}

    def parse_coverage_output(self, coverage_text: str) -> Dict[str, Dict]:
        """解析覆盖率输出文本"""
        coverage_data = {}
        lines = coverage_text.strip().split("\n")

        # 找到覆盖率表格的开始
        in_table = False
        for line in lines:
            if line.startswith("Name") and "Stmts" in line:
                in_table = True
                continue
            if in_table and line.startswith("---"):
                continue
            if in_table and not line.strip():
                break

            if in_table:
                # 解析每一行
                parts = re.split(r"\s+", line.strip())
                if len(parts) >= 5:
                    module_name = parts[0]
                    stmts = int(parts[1])
                    miss = int(parts[2])
                    cover = int(parts[3].rstrip("%"))
                    missing_lines = parts[4] if len(parts) > 4 else ""

                    coverage_data[module_name] = {
                        "statements": stmts,
                        "missed": miss,
                        "coverage": cover,
                        "missing": missing_lines,
                    }

        return coverage_data

    def get_missing_lines(self, module_path: str, missing_ranges: str) -> List[int]:
        """将缺失范围字符串转换为具体的行号列表"""
        missing_lines = []

        if not missing_ranges:
            return missing_lines

        # 解析如 "116, 141-143, 201-211" 这样的字符串
        parts = missing_ranges.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                missing_lines.extend(range(start, end + 1))
            else:
                try:
                    missing_lines.append(int(part))
                except ValueError:
                    pass

        return sorted(missing_lines)

    def read_source_lines(
        self, module_path: str, line_numbers: List[int]
    ) -> Dict[int, str]:
        """读取指定模块中特定行的源代码"""
        source_file = (
            self.project_root / module_path.replace("/", "\\").replace(".", "\\")
            + ".py"
        )
        if not source_file.exists():
            # 尝试其他可能的路径
            source_file = (
                self.project_root
                / "src"
                / "cchess"
                / Path(module_path).with_suffix(".py")
            )

        if not source_file.exists():
            return {}

        with open(source_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        result = {}
        for line_num in line_numbers:
            if 0 <= line_num - 1 < len(lines):
                result[line_num] = lines[line_num - 1].rstrip()

        return result

    def analyze_missing_code(self, coverage_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """分析未覆盖的代码"""
        analysis = {}

        for module_name, data in coverage_data.items():
            if data["missed"] == 0:
                continue

            missing_lines = self.get_missing_lines(module_name, data["missing"])
            source_lines = self.read_source_lines(module_name, missing_lines)

            # 按功能分类未覆盖的代码
            categories = {
                "exception_handling": [],
                "edge_cases": [],
                "unused_methods": [],
                "performance_optimizations": [],
                "unimplemented_features": [],
                "other": [],
            }

            for line_num, line in source_lines.items():
                line_text = line.strip()

                if (
                    not line_text
                    or line_text.startswith("#")
                    or line_text.startswith('"""')
                ):
                    continue

                # 分类逻辑
                if any(
                    keyword in line_text.lower()
                    for keyword in ["raise", "except", "try:", "finally:"]
                ):
                    categories["exception_handling"].append((line_num, line_text))
                elif any(
                    keyword in line_text.lower()
                    for keyword in [
                        "if not",
                        "if not in",
                        "if not isinstance",
                        "if not exists",
                    ]
                ):
                    categories["edge_cases"].append((line_num, line_text))
                elif any(
                    keyword in line_text.lower() for keyword in ["def ", "async def "]
                ):
                    # 检查是否是未使用的函数
                    categories["unused_methods"].append((line_num, line_text))
                elif any(
                    keyword in line_text.lower()
                    for keyword in ["cache", "optimize", "performance", "memoize"]
                ):
                    categories["performance_optimizations"].append(
                        (line_num, line_text)
                    )
                elif any(
                    keyword in line_text.lower()
                    for keyword in ["todo", "fixme", "xxx", "not implemented", "pass"]
                ):
                    categories["unimplemented_features"].append((line_num, line_text))
                else:
                    categories["other"].append((line_num, line_text))

            analysis[module_name] = {
                "coverage": data["coverage"],
                "missed_statements": data["missed"],
                "total_statements": data["statements"],
                "categories": categories,
            }

        return analysis

    def generate_report(
        self, analysis: Dict[str, Dict], output_file: str = None
    ) -> str:
        """生成详细的分析报告"""
        report_lines = []

        # 标题
        report_lines.append("# 测试覆盖率分析报告")
        report_lines.append("")

        # 汇总统计
        total_modules = len(analysis)
        low_coverage = sum(1 for data in analysis.values() if data["coverage"] < 70)
        medium_coverage = sum(
            1 for data in analysis.values() if 70 <= data["coverage"] < 90
        )
        high_coverage = sum(1 for data in analysis.values() if data["coverage"] >= 90)

        report_lines.append("## 汇总统计")
        report_lines.append(f"- 分析模块数: {total_modules}")
        report_lines.append(f"- 低覆盖率 (<70%): {low_coverage} 个")
        report_lines.append(f"- 中等覆盖率 (70-90%): {medium_coverage} 个")
        report_lines.append(f"- 高覆盖率 (≥90%): {high_coverage} 个")
        report_lines.append("")

        # 按覆盖率排序
        sorted_modules = sorted(analysis.items(), key=lambda x: x[1]["coverage"])

        for module_name, data in sorted_modules:
            report_lines.append(f"## {module_name}")
            report_lines.append(f"- 覆盖率: {data['coverage']}%")
            report_lines.append(
                f"- 未覆盖语句: {data['missed_statements']}/{data['total_statements']}"
            )
            report_lines.append("")

            # 按类别显示未覆盖代码
            categories = data["categories"]
            for category_name, items in categories.items():
                if items:
                    report_lines.append(
                        f"### {self._get_category_display_name(category_name)}"
                    )
                    for line_num, line_text in items[:10]:  # 只显示前10行
                        report_lines.append(f"- 第 {line_num} 行: `{line_text}`")
                    if len(items) > 10:
                        report_lines.append(f"- ... 还有 {len(items) - 10} 行未显示")
                    report_lines.append("")

            if any(len(items) > 0 for items in categories.values()):
                report_lines.append("### 建议")
                report_lines.append(self._generate_suggestions(categories))
                report_lines.append("")

            report_lines.append("---")
            report_lines.append("")

        report = "\n".join(report_lines)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)

        return report

    def _get_category_display_name(self, category: str) -> str:
        """获取分类的显示名称"""
        names = {
            "exception_handling": "异常处理代码",
            "edge_cases": "边界条件处理",
            "unused_methods": "未使用的方法",
            "performance_optimizations": "性能优化代码",
            "unimplemented_features": "未实现的功能",
            "other": "其他未覆盖代码",
        }
        return names.get(category, category)

    def _generate_suggestions(self, categories: Dict[str, List]) -> str:
        """生成改进建议"""
        suggestions = []

        if categories.get("exception_handling"):
            suggestions.append("- 添加异常处理测试用例，模拟各种错误场景")

        if categories.get("edge_cases"):
            suggestions.append("- 添加边界条件测试，如空输入、越界值、特殊字符等")

        if categories.get("unused_methods"):
            suggestions.append("- 检查这些方法是否真的需要，或者是否需要添加相应的测试")

        if categories.get("performance_optimizations"):
            suggestions.append("- 添加性能测试用例，验证优化代码的正确性")

        if categories.get("unimplemented_features"):
            suggestions.append("- 实现这些功能并添加测试，或标记为 TODO")

        if categories.get("other"):
            suggestions.append("- 添加常规测试用例覆盖这些代码路径")

        return "\n".join(suggestions) if suggestions else "无特定建议"


def main():
    """主函数"""
    if len(sys.argv) > 1:
        coverage_file = sys.argv[1]
        with open(coverage_file, "r", encoding="utf-8") as f:
            coverage_text = f.read()
    else:
        # 如果没有提供文件，运行测试并获取覆盖率
        import subprocess

        print("运行测试并获取覆盖率数据...")
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_coverage.py",
                "-x",
                "-q",
                "--cov=src/cchess",
                "--cov-report=term-missing",
            ],
            capture_output=True,
            text=True,
        )
        coverage_text = result.stdout

    analyzer = CoverageAnalyzer()
    coverage_data = analyzer.parse_coverage_output(coverage_text)
    analysis = analyzer.analyze_missing_code(coverage_data)

    report = analyzer.generate_report(analysis, "coverage_analysis_report.md")

    print("覆盖率分析报告已生成: coverage_analysis_report.md")

    # 打印关键发现
    print("\n关键发现:")
    for module_name, data in sorted(analysis.items(), key=lambda x: x[1]["coverage"]):
        if data["coverage"] < 50:
            print(f"⚠️  {module_name}: {data['coverage']}% (严重不足)")
        elif data["coverage"] < 70:
            print(f"⚠️  {module_name}: {data['coverage']}% (需要改进)")
        elif data["coverage"] < 90:
            print(f"✓   {module_name}: {data['coverage']}% (良好)")
        else:
            print(f"✓✓  {module_name}: {data['coverage']}% (优秀)")


if __name__ == "__main__":
    main()

"""
Copyright (C) 2024  walker li <walker8088@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import pathlib
import sys

from .game import Game


def print_game(game):
    """将棋局信息、初始盘面和走子文本打印到标准输出。"""

    print("\n=====================================")
    for key, v in game.info.items():
        if v:
            print(f"{key} : {v}")

    game.print_init_board()
    print("-------------------------------------")
    if game.annote:
        print(game.annote)
        print("-------------------------------------")

    game.print_text_moves(steps_per_line=5, show_annote=True)


def convert_format(input_file, output_file):
    """读取一种格式的棋谱文件并转换为另一种格式。

    支持的转换:
        pgn -> xqf, cbf -> xqf
        xqf -> pgn
    """
    in_ext = pathlib.Path(input_file).suffix.lower()
    out_ext = pathlib.Path(output_file).suffix.lower()

    if in_ext not in (".pgn", ".xqf", ".cbf"):
        print(f"不支持的输入格式: {in_ext} (支持 pgn, xqf, cbf)")
        sys.exit(-1)

    if out_ext not in (".xqf", ".pgn"):
        print(f"不支持的输出格式: {out_ext} (支持 xqf, pgn)")
        sys.exit(-1)

    if in_ext == out_ext:
        print(f"输入和输出格式相同: {in_ext}")
        sys.exit(-1)

    try:
        game = Game.read_from(input_file)
    except (OSError, ValueError) as e:
        print(f"读取文件失败: {e}")
        sys.exit(-1)

    if out_ext == ".xqf":
        from .io_xqf import XQFWriter  # pylint: disable=import-outside-toplevel

        writer = XQFWriter(game)
        writer.save(output_file)
    elif out_ext == ".pgn":
        game.save_to_pgn(output_file)

    print(f"转换成功: {input_file} ({in_ext[1:]}) -> {output_file} ({out_ext[1:]})")


def main():
    """命令行入口：读取棋谱并打印内容，或进行格式转换。"""
    parser = argparse.ArgumentParser(prog="python -m cchess")
    parser.add_argument("-r", "--readfile", help="read pgn,xqf,cbf and cbl file")
    parser.add_argument("-i", "--input", help="input file for format conversion")
    parser.add_argument("-o", "--output", help="output file for format conversion")
    args = parser.parse_args()

    if args.input and args.output:
        convert_format(args.input, args.output)
        return

    file_name = args.readfile
    if file_name:
        ext = pathlib.Path(file_name).suffix.lower()
        if ext == ".cbl":
            lib = Game.read_from_lib(file_name)
            print(lib["name"])
            for game in lib["games"]:
                print_game(game)
        else:
            try:
                game = Game.read_from(file_name)
            except (OSError, ValueError) as e:
                print(e)
                sys.exit(-1)
            print_game(game)


if __name__ == "__main__":
    main()

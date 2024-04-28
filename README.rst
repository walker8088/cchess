
cchess
======

cchess是一个Python版的中国象棋库，主要功能如下:

棋盘显示
--------

.. code-block::

   board_strs = board.text_view()
   print()
   for s in board_strs:
       print(s)
   #or    
   board.print_board()


走子(内部格式), 中文显示
------------------------

.. code-block::

   move = board.copy().move((0,0),(0,1))
   print(move.to_text())


走子(ICCS纵线格式),中文显示
---------------------------

.. code-block::

   move = board.copy().move_iccs('a0a1')
   print(move.to_text())


走子(中文格式,尚待完善),中文显示
--------------------------------

.. code-block::

   move = board.copy().move_text('车九进一')
   print(move.to_text())


产生某个棋子的合法走子
----------------------

.. code-block::

   moves = board.create_piece_moves((0,0))
   for mv in moves:
       move = board.copy().move(*mv)
       print(move.to_text())


产生所有合法走子
----------------

.. code-block::

   moves = board.create_moves()
   for mv in moves:
       move = board.copy().move(*mv)
       print(move.to_text())


将军检测
--------

.. code-block::

   board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 w - - 0 1') 
   print(board.is_checking()) #True


将死对方检测
------------

.. code-block::

   print(board.is_win())      #True


走子被将军检测
--------------

.. code-block::

   board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 b - - 0 1')
   mv = move.from_iccs('d9e9') 
   print(board.is_checked_move(*mv)) #True


被对方将死检测
--------------

.. code-block::

   print(board.is_dead())    #True


读取xqf文件, 显示棋谱
---------------------

.. code-block::

   #8.读取xqf文件, 显示棋谱
   game = read_from_xqf("WildHouse.xqf")
   game.init_board.print_board()
   board_strs = game.init_board.text_view()
   print()
   for s in board_strs:
       print(s)

   game.print_text_moves()


以上参见demo/demo_base.py

加载引擎进行对弈
----------------

参见examples/end_game.py

cchess库使用pytest进行单元测试，使用pytest-cov进行覆盖检查，目标实现100%覆盖(目前还未完成)。

测试执行：pytest -v --cov=cchess .\tests\

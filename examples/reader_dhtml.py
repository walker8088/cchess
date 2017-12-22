# -*- coding: utf-8 -*-
'''
Copyright (C) 2014  walker li <walker8088@gmail.com>

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
'''

import os
import struct

from bs4 import BeautifulSoup
import xml.etree.cElementTree as et

from cchess import *

#-----------------------------------------------------#
def read_from_dhtml(html_page):
    res_dict = __parse_dhtml(html_page)
    game = read_from_txt(res_dict['moves'], res_dict['init'])
    return game

#-----------------------------------------------------#
def __str_between(src, begin_str, end_str):
    first = src.find(begin_str) + len(begin_str)
    last = src.find(end_str)
    if (first != -1) and (last != -1):
        return src[first:last]
    else:
        return None


def __str_between2(src, begin_str, end_str):
    first = src.find(begin_str) + len(begin_str)
    last = src.find(end_str)
    if last > first:
        return src[first:last]
    if last == -1:
        return None

    src2 = src[last + len(end_str):]
    f2 = src2.find(begin_str) + len(begin_str)
    l2 = src2.find(end_str)
    if l2 > f2:
        return src2[f2:l2]
    else:
        return None


def __parse_dhtml(html_page):
    result_dict = {}
    text = html_page.decode('GB18030')
    result_dict['event'] = __str_between(text, '[DhtmlXQ_event]',
                                         '[/DhtmlXQ_event]')
    if result_dict['event']:
        result_dict['event'] = result_dict['event']

    result_dict['title'] = __str_between(text, '[DhtmlXQ_title]',
                                         '[/DhtmlXQ_title]')
    if result_dict['title']:
        result_dict['title'] = result_dict['title']

    result_dict['result'] = __str_between(text, '[DhtmlXQ_result]',
                                          '[/DhtmlXQ_result]')
    if result_dict['result']:
        result_dict['result'] = result_dict['result']

    init = __str_between(text, '[DhtmlXQ_binit]', '[/DhtmlXQ_binit]')
    result_dict['init'] = init.encode('utf-8') if init else None
    moves = __str_between2(text, '[DhtmlXQ_movelist]', '[/DhtmlXQ_movelist]')
    result_dict['moves'] = moves.encode('utf-8') if moves else None

    return result_dict


#-----------------------------------------------------#
if __name__ == '__main__':
    pass
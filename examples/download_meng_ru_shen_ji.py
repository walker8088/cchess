# coding:utf-8
import sys
import re
import requests

from bs4 import BeautifulSoup

#from tinydb import TinyDB, Query

sys.path.append("..")
from cchess import *

url_base = 'http://www.dpxq.com/hldcg/share/chess_%E8%B1%A1%E6%A3%8B%E8%B0%B1%E5%A4%A7%E5%85%A8/%E8%B1%A1%E6%A3%8B%E8%B0%B1%E5%A4%A7%E5%85%A8-%E5%8F%A4%E8%B0%B1%E6%AE%8B%E5%B1%80/%E6%A2%A6%E5%85%A5%E7%A5%9E%E6%9C%BA/%E6%A2%A6%E5%85%A5%E7%A5%9E%E6%9C%BA/'

games = []


def open_url(url):
    req = requests.get(url)
    if req.status_code != 200:
        return None
    return req.content


def parse_games(html):
    games = []
    soup = BeautifulSoup(html, 'lxml')
    for td in soup.find_all('td'):
        if td.a == None or len(td.a.text) == 0:
            continue
        title = unicode(td.a.text)
        if title.encode('utf-8')[0] in [
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
        ]:
            # print title, td.a['href']
            games.append([title, td.a['href']])
    return games


html = open_url(url_base + "1.html")
if html == None:
    sys.exit(-1)
games1 = parse_games(html.decode("GB2312"))

html = open_url(url_base + "2.html")
if html == None:
    sys.exit(-1)
games2 = parse_games(html.decode("GB2312"))

games = games1 + games2

games.sort(key=lambda x: x[0])

bad_files = []
#db = TinyDB(u'梦入神机.jdb')
games_result = []
for it in games[:]:
    game_info = {}
    html_page = open_url("http://www.dpxq.com" + it[1])
    if html_page == None:
        continue

    game = read_from_dhtml(html_page)
    if not game:
        bad_files.append(it[0])
        continue

    board_txt = game.dump_init_board()

    print it[0]

    if game.init_board.move_side != ChessSide.RED:
        game.init_board.move_side = ChessSide.RED
        # print "Erorr",game.init_board.move_side

    game_info['name'] = it[0][3:]
    game_info['fen'] = game.init_board.to_short_fen()
    moves = game.dump_std_moves()
    game_info['moves'] = moves
    game_info['move_len'] = len(moves[0]) if len(
        moves) > 0 else 0  # ','.join(moves[0]) if len(moves) > 0 else ''
    games_result.append(game_info)
    game.print_init_board()
    game.print_chinese_moves()
    # db.insert(game_info)

# db.close()

games_result.sort(key=lambda x: x['move_len'])

if len(bad_files) > 0:
    print "BAD FILES:",
    for it in bad_files:
        print it,
    print 'End.'

with open(u"梦入神机.eglib", "wb") as f:
    for it in games_result:
        if it['move_len']:
            f.write("%s|%s|%s\n" % (it['name'].encode('utf-8'), it['fen'],
                                    ','.join(it['moves'][0])))
        else:
            f.write("%s|%s\n" % (it['name'].encode('utf-8'), it['fen']))

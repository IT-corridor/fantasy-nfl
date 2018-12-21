"""
Use Pro Football Reference
"""
import urllib2

from bs4 import BeautifulSoup

import re
import os
from os import sys, path
import django
from django.db.models import Q


import datetime

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *

def sync(type_, val):
    # fit into roto
    val = val.strip().strip('@')
    conv = {
        'team': {
            'NOR': 'NO',
            'GNB': 'GB',
            'SFO': 'SF',
            'TAM': 'TB',
            'NWE': 'NE',
            'KAN': 'KC'
        },
        'name': {
        }
    }
    return conv[type_][val] if val in conv[type_] else val

def _C(val_dict, field):
    return float(val_dict.get(field, '0').strip() or '0')

def scrape(week):
    url = 'https://www.pro-football-reference.com/years/2018/week_{}.htm'.format(week)
    print "||" + url
    response = urllib2.urlopen(url)
    r = response.read()
    soup = BeautifulSoup(r, "html.parser")
    links = []
    for ii in soup.find_all("td", {"class": "right gamelink"}):
        link = ii.find('a').get('href')
        links.append(link)

    for game_link in links:
        url = 'https://www.pro-football-reference.com' + game_link
        print "|| - " + url
        response = urllib2.urlopen(url)
        body = response.read()

        soup = BeautifulSoup(body, "html.parser")
        game_results = soup.find_all("div", {"class": "score"})
        home_score = int(game_results[0].text.strip())
        away_score = int(game_results[1].text.strip())

        tbl_text = body.split('<div class="overthrow table_container" id="div_player_offense">')[1].split('</div>')[0]
        soup = BeautifulSoup(tbl_text, "html.parser")
        table = soup.find("table", {"id":"player_offense"})
        player_rows = table.find("tbody")
        players = player_rows.find_all("tr")

        home_team = sync('team', players[-1].find("td", {"data-stat":"team"}).text.strip())
        away_team = sync('team', players[0].find("td", {"data-stat":"team"}).text.strip())

        game_info = {
            home_team: [away_team, '', 'W' if home_score > away_score else 'T' if home_score == away_score else 'L'],
            away_team: [home_team, '@', 'L' if home_score > away_score else 'T' if home_score == away_score else 'W']
        }

        for player in players:
            # try:
                if player.get('class'): # ignore header
                    continue

                name = player.find("th", {"data-stat":"player"}).text.strip()
                name = sync('name', name)
                game_date = game_link[11:19]
                date = datetime.datetime.strptime(game_date, '%Y%m%d')
                uid = player.find("th", {"data-stat":"player"}).get('data-append-csv')

                defaults = {
                    'name': name,
                    'week_num': week
                }

                fields = ['team', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_rating', 'pass_sacked', 
                          'pass_sacked_yds', 'pass_long', 'rush_att', 'rush_yds', 'rush_td', 'rush_long', 
                          'targets', 'rec', 'rec_yds', 'rec_td', 'rec_long', 'fumbles', 'fumbles_lost']

                for ii in fields:
                    field = player.find("td", {"data-stat": ii}).text.replace('%', '').strip()
                    if field:
                        defaults[ii] = field

                defaults['team'] = sync('team', defaults['team'])
                defaults['opp'] = game_info[defaults['team']][0]
                defaults['game_location'] = game_info[defaults['team']][1]
                defaults['game_result'] = game_info[defaults['team']][2]
                defaults['fpts'] = 0.1 * _C(defaults, 'rush_yds') + 6 * _C(defaults, 'rush_td') \
                                 + 0.04 * _C(defaults, 'pass_yds') + 4 * _C(defaults, 'pass_td') \
                                 - _C(defaults, 'pass_int') + 0.1 * _C(defaults, 'rec_yds') \
                                 + 6 * _C(defaults, 'rec_td') + 0.5 * _C(defaults, 'rec')                

                first_name, last_name = parse_name(name)
                q = Q(first_name__iexact=first_name) & Q(last_name__iexact=last_name)
                if name == 'Ryan Griffin':
                    q &= Q(team=defaults['team'])
                player_ = Player.objects.filter(q)
                if player_:
                    defaults['pos'] = player_.first().position
                    # update avatar for possible new players
                    avatar = 'https://d395i9ljze9h3x.cloudfront.net/req/20180910/images/headshots/{}_2018.jpg'.format(uid)
                    player_.update(avatar=avatar, gid=uid)
                else:
                    print name, defaults['team'], date, '=================='
                # print(defaults)
                PlayerGame.objects.update_or_create(uid=uid, date=date, defaults=defaults)
            # except Exception as e:
                # print(defaults)
                # print('------------------------------')
                # print(e)

if __name__ == "__main__":
    for week in range(2, 5):
        scrape(week)
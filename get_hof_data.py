#!/usr/bin/env python

from bs4 import BeautifulSoup
from joblib import Parallel,delayed
from player_html import get_all_html
from player_index import get_all_players
from player_table import get_table

import multiprocessing
import pandas as pd
import re

def get_career_stats(soup):
    '''
    Scrapes the stats pullout section on a player's page
    PARAMS  soup: BeautifulSoup of player's HTML
    RETURN  career_games: # of career games
            career_win_shares: # total career win shares
            hof_as_player: if the player was inducted into the HoF as a player (as opposed to coach)
    '''
    # initialized to None instead of 0 to identify missing data
    career_games=None
    career_win_shares=None
    hof_as_player=None

    stats_pullout=soup.find('div',class_='stats_pullout')

    # if results are found in the soup
    if (stats_pullout is not None):
        # career games
        career_games=int(stats_pullout.find('div',class_='p1').find_all('p')[1].getText())

        # career win shares
        career_win_shares=stats_pullout.find('div',class_='p3').find_all('p')[3].getText()
        if (career_win_shares!='-'):
            career_win_shares=float(career_win_shares)

        # if the player was inducted in the HoF as a player
        # this removes HoF coaches from the training data (rightfully so)
        hof_as_player=1*(soup.find(text=re.compile('Inducted as Player')) is not None)
    return(career_games,career_win_shares,hof_as_player)

def get_n_chips(soup):
    '''
    Scrapes the bling section on a player's page
    PARAMS  soup: BeautifulSoup of player's HTML
    RETURN  n_chips: # of NBA championships
    '''
    # here if the data is missing, it means 0 chips
    n_chips=0

    bling=soup.find('ul',id='bling')

    # if results are found in the soup
    if (bling is not None):
        bling_list=bling.find_all('li')
        for j in range(len(bling_list)):
            b=bling_list[j].getText().lower()
            # all star appearances are not computed from here because it does not distinguish NBA/ABA
            # number of non-ABA championships
            if ('nba champ' in b):
                # the number of championships is styled as either Nx NBA Champ or yyyy-yy NBA Champ (1x NBA Champ)
                champ_banner=b.split('x')
                n_chips=int(champ_banner[0]) if (len(champ_banner)>1) else 1
    return(n_chips)

def get_adv_stats(soup):
    '''
    Scrapes the Advanced table on a player's page
    PARAMS  soup: BeautifulSoup of a player's HTML
    RETURN  aba_years: # years spent in ABA
            nba_asg: # of NBA all-star games
            peak_ws: highest win shares in an NBA season
    '''
    # win shares can be missing
    aba_years=0
    nba_asg=0
    peak_ws=None

    adv_table=get_table(soup,'div_advanced')

    # if results are found in the soup
    if (adv_table is not None):
        # look at season rows only (not career summaries)
        adv_table=adv_table.loc[adv_table['Season'].str.contains('-')]

        # number of seasons in the ABA
        aba_years=adv_table.loc[adv_table['Lg']=='ABA','Season'].nunique()

        # keep only NBA seasons
        nba_seasons=adv_table.loc[adv_table['Lg']!='ABA'].reset_index(drop=True)
        # all-star game appearances and peak win shares are only for NBA seasons
        if (nba_seasons.shape[0]>0):
            # number of NBA all-star games
            nba_asg=nba_seasons.loc[nba_seasons['asg']=='*','Season'].nunique()

            # peak win shares in the NBA (BAA is included)
            try:
                peak_ws=max(float(ws) for ws in nba_seasons['WS'] if ws!='')
                # use WS/48 if it's available because it has more decimal places
                mp,ws48=tuple(nba_seasons.loc[nba_seasons['WS']==str(peak_ws),['MP','WS/48']].values[0])
                if (mp!='' and ws48!=''):
                    peak_ws=float(mp)*float(ws48)/48
            # some players like Dan King do not have win shares recorded
            except ValueError:
                peak_ws=None
    return(aba_years,nba_asg,peak_ws)

def get_leaderboard(soup):
    '''
    Scrapes the Appearances on Leaderboards, Awards, and Honors section on a player's page
    PARAMS  soup: BeautifulSoup of a player's HTML
    RETURN  leaderboard_points: total # of leaderboard points
            hof_pr: Basketball-Reference's reported HoF probability
    '''
    leaderboard_points=0
    # there will be no distinction between having 0 HoF probability and not being eligible
    # those not yet eligible will be listed as having 0 probability of going to HoF
    hof_pr=0

    leaderboard=soup.find(text=re.compile('div_leaderboard'))

    if (leaderboard is not None):
        leaderboard=BeautifulSoup(leaderboard,'lxml')

        # relevant leaderboard categories
        cat_list=['leaderboard_pts','leaderboard_trb','leaderboard_ast','leaderboard_mp','leaderboard_stl','leaderboard_blk']
        for cat in cat_list:
            rows=leaderboard.find('div',id=cat)
            if (rows is not None):
                rows=rows.find_all('tr')
                # '-' in item omits career stats
                # excludes ABA leaderboard points
                leaderboard_points+=sum(11-int(re.search(r'\((.*?)\)',l).group(1)[0:-2]) for l in (item for item in (s.getText() for s in rows) if ('-' in item) and ('ABA' not in item)))

        # HoF probability
        hof_panel=leaderboard.find('div',id='leaderboard_hof_prob')
        if (hof_panel is not None):
            hof_panel=hof_panel.find('td')
            hof_pr=float(hof_panel.getText().split(' ')[1][0:-1])/100
    return(leaderboard_points,hof_pr)

def get_hof_data(soup):
    '''
    Retrieves all relevant HoF probability data for a particular player
    PARAMS  soup: BeautifulSoup of a player's HTML
    RETURN  list of all relevant HoF data
    '''
    career_games,career_win_shares,hof_as_player=get_career_stats(soup)
    n_chips=get_n_chips(soup)
    aba_years,nba_asg,peak_ws=get_adv_stats(soup)
    leaderboard_points,hof_pr=get_leaderboard(soup)
    return([career_games,career_win_shares,peak_ws,aba_years,n_chips,nba_asg,leaderboard_points,hof_as_player,hof_pr])

def get_hof_data():
    '''
    Retrieves all relevant HoF probability data for all players
    PARAMS
    RETURN  pandas DataFrame of all relevant data
    '''
    num_cores=multiprocessing.cpu_count()

    all_players=get_all_players()
    n_players=all_players.shape[0]
    all_html=get_all_html(all_players)
    print('')

    print('converting HTML to pandas DataFrame... ',end='')
    multi_out=Parallel(n_jobs=num_cores)(delayed(get_hof_data_row)(BeautifulSoup(all_html[all_players.loc[i,'url']],'lxml')) for i in range(n_players))
    print('done')

    hof_cols=pd.DataFrame(multi_out,columns=['career_games','career_win_shares','peak_ws','aba_years','n_chips','nba_asg','leaderboard_points','hof_as_player','hof_pr'])
    hof_data=pd.concat([all_players,hof_cols],axis=1)
    return(hof_data)

def main():
    hof_data=get_hof_data()
    hof_data.to_csv('data/hof.csv',index=False)
    print('saved to data/hof.csv')

if (__name__=='__main__'):
    main()

#!/usr/bin/env python

from bs4 import BeautifulSoup
from datetime import datetime
from joblib import Parallel,delayed

import argparse
import multiprocessing
import pandas as pd
import requests
import string

def arg_parser():
    parser=argparse.ArgumentParser(description='gathers a list all past and present NBA players from Basketball Reference')
    parser.add_argument('-t','--tag',default='all_players_'+datetime.today().strftime('%Y-%m-%d')+'.csv',help='filename for saved csv')
    return(parser)

def clean_row(i,stats):
    player_th=stats[i].find_all('th')[0]
    player_name=player_th.getText()
    player_stats=[td.getText() for td in stats[i].find_all('td')]
    player_url=player_th.find_all('a')[0]['href'] if (len(player_th.find_all('a'))==1) else ''
    player_is_active=len(player_th.find_all('strong'))==1
    player_is_hof='*' in player_name
    return([player_name]+player_stats+[player_url,player_is_active,player_is_hof])

def process_request(url_request):
    html=url_request.content
    soup=BeautifulSoup(html,'lxml')

    # the first row is column names
    rows=soup.find_all('tr')
    stats=rows[1:]

    # retrieve the row of stats for the current player
    out=[]
    for i in range(len(stats)):
        out.append(clean_row(i,stats))
    return(out)

def send_request(letter):
    url='https://www.basketball-reference.com/players/'+letter
    url_request=requests.get(url)
    if (url_request.status_code==200):
        return(process_request(url_request))

def get_data():
    num_cores=multiprocessing.cpu_count()
    alphabet=string.ascii_lowercase
    results=Parallel(n_jobs=num_cores)(delayed(send_request)(alphabet[i]) for i in range(len(alphabet)))

    # turning lists into pandas DataFrame
    OUT=pd.DataFrame(results[0])
    for i in range(1,len(results)):
        OUT=pd.concat([OUT,pd.DataFrame(results[i])])
    OUT.columns=['Player','From','To','Pos','Ht','Wt','Birth Date','Colleges','url','is_active','in_hof']
    return(OUT.reset_index(drop=True))

def main():
    ap=arg_parser()
    args=ap.parse_args()
    get_data().to_csv('data/'+args.tag,index=False)
    print('saved to data/'+args.tag)

if (__name__ == '__main__'):
    main()

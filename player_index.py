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
    return parser

def clean_row(i,stats):
    '''
    Prepares the data for player i
    PARAMS  i: int indicating the current player
            stats: BeautifulSoup of a player's basic information
    RETURN  list of basic information
    '''
    player_th=stats[i].find_all('th')[0]
    player_name=player_th.getText()
    player_stats=[td.getText() for td in stats[i].find_all('td')]
    player_url=player_th.find_all('a')[0]['href'] if (len(player_th.find_all('a'))==1) else ''
    player_is_active=len(player_th.find_all('strong'))==1
    player_is_hof='*' in player_name
    return [player_name]+player_stats+[player_url,player_is_active,player_is_hof]

def process_request(url_request):
    '''
    Takes a URL request and returns relevant basic information on the player
    PARAMS  url_request: response of the URL requested
    RETURN  out: list of basic information
    '''
    html=url_request.content
    soup=BeautifulSoup(html,'lxml')

    # the first row is column names
    rows=soup.find_all('tr')
    stats=rows[1:]

    # retrieve the row of stats for the current player
    out=[]
    for i in range(len(stats)):
        out.append(clean_row(i,stats))
    return out

def send_request(letter):
    '''
    Requests the players whose last names begin with a certain letter
    PARAMS  letter: string of the letter being considered
    RETURN  list of basic information on the player
    '''
    url='https://www.basketball-reference.com/players/'+letter
    url_request=requests.get(url)
    if (url_request.status_code==200):
        return process_request(url_request)

def get_all_players():
    '''
    Retrieves basic information for all players in Basketball-Reference
    PARAMS
    RETURN  OUT: pandas DataFrame with the basic information
    '''
    num_cores=multiprocessing.cpu_count()
    alphabet=string.ascii_lowercase
    results=Parallel(n_jobs=num_cores)(delayed(send_request)(alphabet[i]) for i in range(len(alphabet)))

    # turning lists into pandas DataFrame
    OUT=pd.DataFrame(results[0])
    for i in range(1,len(results)):
        OUT=pd.concat([OUT,pd.DataFrame(results[i])])
    OUT.columns=['Player','From','To','Pos','Ht','Wt','Birth Date','Colleges','url','is_active','in_hof']
    OUT=OUT.reset_index(drop=True)

    # removing stray asterisks
    OUT['Player']=OUT['Player'].str.strip('*')

    # George Karl is missing his height for some reason
    OUT.loc[OUT['Player']=='George Karl','Ht']='6-2'

    # converting height to inches
    OUT['Ht']=[int(fi[0])*12+int(fi[1]) for fi in (ht.split('-') for ht in OUT['Ht'])]
    return OUT

def main():
    ap=arg_parser()
    args=ap.parse_args()
    get_all_players().to_csv('data/'+args.tag,index=False)
    print('saved to data/'+args.tag)

if __name__ == '__main__':
    main()

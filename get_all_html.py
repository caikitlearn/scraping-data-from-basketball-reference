#!/usr/bin/env python

import requests
import pickle
import sys
from get_all_players import get_data

def get_player_html(url):
    '''
    Sends a request to Basketball-Reference for a player's page and returns the HTML
    PARAMS:  url: suffix URL of the player (e.g. '/players/o/oladivi01.html')
    RETURNS: html: bytes object containing the HTML of the player's page
    '''
    html=None
    try:
        html=requests.get('https://www.basketball-reference.com'+url).content
    # sometimes the request is refused if we are sending too many at a time
    except requests.exceptions.ConnectionError:
        print('Connection refused for: '+url)
    return(html)

def get_all_html():
    '''
    Stores the HTML of every player on Basketball-Reference into a dictionary
    PARAMS:
    RETURNS: all_html: dictionary of all players with URL as keys and HTML as values
    '''
    # get a DataFrame of all players
    all_players=get_data()
    n_players=all_players.shape[0]

    # George Karl is missing his height for some reason
    all_players.loc[all_players['Player']=='George Karl','Ht']='6-2'
    # converting height to inches
    all_players['Ht']=[int(fi[0])*12+int(fi[1]) for fi in (ht.split('-') for ht in all_players['Ht'])]

    # save the HTML of each player page to a dictionary
    # this could be parallelized but that increases the chances of a ConnectionError
    all_html={}
    for i in range(n_players):
        url=all_players['url'].iloc[i]
        all_html[url]=get_player_html(url)
        sys.stdout.write('\rprocessed player '+str(i+1)+' of '+str(n_players))
        sys.stdout.flush()
    print('\n')
    return(all_html)

def main():
    all_html=get_all_html()
    pickle.dump(all_html,open('data/all_html.pkl','wb'))
    print('saved to data/all_html.pkl')

if (__name__=='__main__'):
    main()

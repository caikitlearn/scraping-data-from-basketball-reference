#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

def clean_row(i,stats):
    stats_all_a=stats[i].find_all('a')
    left_margin=stats[i].find_all('th')[0].getText() if (stats_all_a==[]) else stats_all_a[0].getText()
    return([left_margin]+[td.getText() for td in stats[i].find_all('td')])

def get_table(soup,tablename):
    # with the exception of the Per Game table, the tables are hiding under HTML comments
    init_search=soup.find_all('div',class_='overthrow table_container')[0] if (tablename=='div_per_game') else soup.find(text=re.compile(tablename))

    if (init_search==None):
        print("no tables found")
        return(None)
    else:
        table_soup=BeautifulSoup(init_search,'lxml') if (tablename!='div_per_game') else init_search

        # find all tabular rows
        rows=table_soup.find_all('tr')

        # find the column names and create an empty data frame with them
        colnames=[th.getText() for th in rows[0].find_all('th')]

        # the actual stats
        stats=rows[1:]

        # put the stats into a DataFrame
        OUT=pd.DataFrame([clean_row(i,stats) for i in range(len(stats))])
        OUT.columns=colnames
        # remove empty rows
        return(OUT.loc[(OUT!='').apply(sum,axis=1).values!=0].reset_index(drop=True))

def main():
    pass

if (__name__=='__main__'):
    main()

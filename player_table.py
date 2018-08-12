from bs4 import BeautifulSoup
import re
import pandas as pd

def clean_row(i,stats):
    '''
    Prepares the data for player i
    PARAMS  i: int indicating the current player
            stats: BeautifulSoup of a player's stats
    RETURN  list of stats
    '''
    stats_all_a=stats[i].find_all('a')
    left_margin=stats[i].find_all('th')[0].getText() if (stats_all_a==[]) else stats_all_a[0].getText()
    return([left_margin]+[td.getText() for td in stats[i].find_all('td')])+['*' if (stats[i].find('span',class_='sr_star')!=None) else '']

def get_table(soup,tablename):
    '''
    Retrieves a particular table on a player's page
    PARAMS  soup: BeautifulSoup of a player's HTML
            tablename: html name of the table of interest
    RETURN  pandas DataFrame of the requested table
    '''
    # with the exception of the Per Game table, the tables are hiding under HTML comments
    init_search=soup.find_all('div',class_='overthrow table_container')[0] if (tablename=='div_per_game') else soup.find(text=re.compile(tablename))

    if (init_search==None):
        return(None)
    else:
        table_soup=BeautifulSoup(init_search,'lxml') if (tablename!='div_per_game') else init_search

        # find all tabular rows
        rows=table_soup.find_all('tr')

        # find the column names and create an empty data frame with them
        # adding an extra column to indicate if the player made the all-star game
        colnames=[th.getText() for th in rows[0].find_all('th')]+['asg']

        # the actual stats
        stats=rows[1:]

        # put the stats into a DataFrame
        OUT=pd.DataFrame([clean_row(i,stats) for i in range(len(stats))])
        OUT.columns=colnames
        # remove empty rows
        return(OUT.loc[(OUT!='').apply(sum,axis=1).values!=0].reset_index(drop=True))

from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import numpy as np
import string

def save_player_directory():

    # iterate through the alphabet and collect all player data
    for letter in range(len(string.ascii_lowercase)):
        url='https://www.basketball-reference.com/players/'+string.ascii_lowercase[letter]
        url_request=requests.get(url)

        # only write to csv if the page exists
        # no players currently have last name starting with x
        if (url_request.status_code==200):
            html=url_request.content
            soup=BeautifulSoup(html,'lxml')

            rows=soup.find_all('tr')

            colnames=[th.getText() for th in rows[0].find_all('th')]
            colnames.append('url')
            colnames.append("isActive")
            colnames.append('inHoF')

            # in the first iteration only, create a new csv
            # to store the data
            if (letter==0):
                newfile=pd.DataFrame(columns=colnames)
                with open('data/all_players.csv','w') as f:
                    newfile.to_csv(f,header=True,index=False)

            # data frame to store the data
            OUT=pd.DataFrame(index=range(len(rows)-1),columns=colnames)

            # the first row is column names
            stats=rows[1:]

            # name is stored as header <th>
            for i in range(len(stats)):
                player_name=stats[i].find_all('th')[0]
                rowdata=[player_name.getText()]

                for td in stats[i].find_all('td'):
                    # the stats
                    rowdata.append(td.getText())

                # finding URL
                if (len(player_name.find_all('a'))==1):
                    rowdata.append(stats[i].find_all('th')[0].find_all('a')[0]['href'])
                else:
                    rowdata.append('')

                # active players are bolded with <strong>
                if (len(player_name.find_all('strong'))==1):
                    rowdata.append(1)
                else:
                    rowdata.append(0)

                # determining hall of fame status
                if ('*' in player_name.getText()):
                    rowdata.append(1)
                else:
                    rowdata.append(0)

                OUT.iloc[i]=rowdata

            with open('data/all_players.csv','a') as f:
                OUT.to_csv(f,header=False,index=False)

def player_table_finder(soup,tablename):

    ## the tables are hiding under HTML comments
    table_text=soup.find(text=re.compile(tablename))

    if (table_text==None):
        print("no tables found")
        return(None)
    else:
        table_soup=BeautifulSoup(table_text,'lxml')

        ## find all tabular rows
        rows=table_soup.find_all('tr')

        ## find the column names and create an empty data frame with them
        colnames=[]
        for th in rows[0].find_all('th'):
            colnames.append(th.getText())

        ## empty data frame
        OUT=pd.DataFrame(index=range(len(rows)-1),columns=colnames)
        OUT['asg']=0

        ## the actual stats
        stats=rows[1:]

        ## populate the empty data frame
        for i in range(len(stats)):
            ## season is under a hyperlink <a>
            ## if there is none found, we've come across a career or team header <th>
            if (stats[i].find_all('a')==[]):
                leftmargin=stats[i].find_all('th')[0].getText()
            else:
                leftmargin=stats[i].find_all('a')[0].getText()

            rowdata=[leftmargin]
            for td in stats[i].find_all('td'):
                rowdata.append(td.getText())
            rowdata.append(1*(stats[i].find('span',class_='sr_star')!=None))
            OUT.iloc[i]=rowdata
        return(OUT)

playerData=pd.read_csv('data/all_players.csv')

playerData['career_games']=0
playerData['career_ws']=0
playerData['hof_pr']=0
playerData['aba_yrs']=0
playerData['hof_as_player']=0

playerData['height']=[int(ht.split('-')[0])*12+int(ht.split('-')[1]) if (not pd.isnull(ht)) else (None) for ht in playerData.Ht.values]
playerData['chips']=0
playerData['l_pts']=0
playerData['peak_ws']=0
playerData['asg']=0

## HoF algorithm requires the following:
## Height (in.)
## NBA championships
## NBA Leaderboard Points (PTS, TRB, AST, MP, STL, BLK)
## NBA Peak Win Shares
## All-Star Game Selections

## player pool includes players who have played a minimum of 400 NBA games
## and were retired by the end of the 2004-05 season
##  excluded HOF players with fewer than 50 win shares

for i in range(playerData.shape[0]):
    if (i%100==0): print(i)

    ##==================================================##
    ##   MAKING SOUP                                    ##
    ##==================================================##
    html=requests.get('https://www.basketball-reference.com'+playerData.url[i]).content
    soup=BeautifulSoup(html,'lxml')

    ##==================================================##
    ##   BIO SECTION                                    ##
    ##==================================================##
    stats_pullout=soup.find('div',class_='stats_pullout')

    ## career games
    playerData.loc[playerData.index[i],'career_games']=int(stats_pullout.find('div',class_='p1').find_all('p')[1].getText())

    ## career win shares
    wsTxt=stats_pullout.find('div',class_='p3').find_all('p')[3].getText()
    if (wsTxt!='-'):
        playerData.loc[playerData.index[i],'career_ws']=float(wsTxt)

    ## if the player was inducted in the HoF as a player
    playerData.loc[playerData.index[i],'hof_as_player']=1*(soup.find(text=re.compile('Inducted as Player'))!=None)

    ##==================================================##
    ##   BLING SECTION                                  ##
    ##==================================================##
    bling=soup.find('ul',id='bling')
    if (bling!=None):
        blingList=bling.find_all('li')
        for j in range(len(blingList)):
            currBling=blingList[j].getText().lower()
            # if ('all star' in currBling):
            #    playerData.loc[playerData.index[i],'asg']=int(currBling.split('x')[0])
            ## NUMBER OF NON-ABA CHAMPIONSHIPS
            if ('nba champ' in currBling):
                nchips=currBling.split('x')
                if (len(nchips)>1):
                    playerData.loc[playerData.index[i],'chips']=int(nchips[0])
                else:
                    playerData.loc[playerData.index[i],'chips']=1

    ##==================================================##
    ##   ADVANCED STATS TABLE                           ##
    ##==================================================##
    advTable=player_table_finder(soup,'div_advanced')
    advTable=advTable[advTable.Season.str.contains('-')]

    ## NUMBER OF YEARS IN ABA
    playerData.loc[playerData.index[i],'aba_yrs']=np.sum((advTable.drop_duplicates('Season').Lg=='ABA').values)

    ## REMOVING ABA SEASONS
    advTable=advTable[~(advTable.Lg.str.contains('ABA'))]
    advTable=advTable.drop_duplicates('Season').reset_index(drop=True)

    ## NUMBER OF NBA ALL-STAR GAMES (NOT ABA)
    playerData.loc[playerData.index[i],'asg']=np.sum(advTable.asg.values)

    ## PEAK WIN SHARES IN NBA (NOT ABA)
    wsList=advTable.WS.values
    wsList=wsList[wsList!=''].astype(float)
    if (len(wsList)>0):
        yrmax=np.argmax(wsList)
        ## if WS/48 is available, we calculate a more precise WS
        if ((advTable['WS/48'].iloc[yrmax]!='') and (advTable.MP.iloc[yrmax]!='')):
            playerData.loc[playerData.index[i],'peak_ws']=float(advTable['WS/48'][yrmax])/48*int(advTable.MP[yrmax])
        else:
            playerData.loc[playerData.index[i],'peak_ws']=wsList[yrmax]

    ##==================================================##
    ##   LEADERBOARD SECTION                            ##
    ##==================================================##
    leaderboard=soup.find(text=re.compile('div_leaderboard'))
    if (leaderboard!=None):
        leaderboard=BeautifulSoup(leaderboard,'lxml')
        lpts=0

        ## LEADERPOINT POINTS
        catList=['leaderboard_mp','leaderboard_ast','leaderboard_stl','leaderboard_pts','leaderboard_trb','leaderboard_blk']
        for cat in catList:
            rows=leaderboard.find('div',id=cat)
            if (rows!=None):
                rows=rows.find_all('tr')
                lpts+=sum([11-int(re.search(r'\((.*?)\)',item.getText()).group(1)[0:-2]) for item in rows if (('-' in item.getText()) and 'ABA' not in item.getText())])
        playerData.loc[playerData.index[i],'l_pts']=lpts

        ## HALL OF FAME PROBABILITY
        hofPanel=leaderboard.find('div',id='leaderboard_hof_prob')
        if (hofPanel!=None):
            hofPanel=hofPanel.find('td')
            playerData.loc[playerData.index[i],'hof_pr']=float(hofPanel.getText().split(' ')[1][0:-1])/100

with open('data/hof_data.csv','w') as f:
    playerData.to_csv(f,header=True,index=False)

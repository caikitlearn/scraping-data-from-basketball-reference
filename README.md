# Tools for Scraping Data from Basketball Reference

## ``get_all_players``
- gets a list of all past and present players and their basic information (name, years in the league, position(s), height, weight, birthday, college(s), Basketball Reference url, active player flag, hall of fame flag) from [``https://www.basketball-reference.com/players/``](https://www.basketball-reference.com/players/)
- ``get_data()`` returns results as a pandas DataFrame
- ``main()`` saves results to csv (see list_of_all_players_2018-07-15.csv)
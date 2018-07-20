# Tools for Scraping Data from Basketball Reference

## ``get_all_players.py``
- gets a list of all past and present players and their basic information (name, years in the league, position(s), height, weight, birthday, college(s), Basketball Reference url, active player flag, hall of fame flag) from [``https://www.basketball-reference.com/players/``](https://www.basketball-reference.com/players/)
- ``get_data()`` returns results as a pandas DataFrame
- ``main()`` saves results to csv (see list_of_all_players_2018-07-17.csv)

## ``get_player_table.py``
- gets a specific table from the player's page using the following tags:
  - Per Game: ``div_per_game``
  - Totals: ``div_totals``
  - Per 36 Minutes: ``div_per_minute``
  - Per 100 Poss: ``div_per_poss``
  - Advanced: ``div_advanced``
- ``get_table()`` returns the corresponding table as a pandas DataFrame
- ``main()`` does nothing

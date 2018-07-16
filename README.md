# Tools for Scraping Data from Basketball Reference

## ``get_all_players.py``
- gets a list of all players and their basic information (name, years in the league, position, height, weight, birthday, college, url, active player, hall of fame status) from ``https://www.basketball-reference.com/players/``
- ``main()`` saves results to csv (see list_of_all_players_2018-07-15.csv)
- ``get_data()`` returns results as a pandas Data Frame
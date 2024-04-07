import requests
import pandas as pd
import json
from .functions import get_possible_leagues_for_page
import time
from .exceptions import InvalidStat, MatchDoesntHaveInfo
import matplotlib.pyplot as plt

class FotMob:
    
    def __init__(self):
        self.player_possible_stats = ['goals',
            'goal_assist',
            '_goals_and_goal_assist',
            'rating',
            'goals_per_90',
            'expected_goals',
            'expected_goals_per_90',
            'expected_goalsontarget',
            'ontarget_scoring_att',
            'total_scoring_att',
            'accurate_pass',
            'big_chance_created',
            'total_att_assist',
            'accurate_long_balls',
            'expected_assists',
            'expected_assists_per_90',
            '_expected_goals_and_expected_assists_per_90',
            'won_contest',
            'big_chance_missed',
            'penalty_won',
            'won_tackle',
            'interception',
            'effective_clearance',
            'outfielder_block',
            'penalty_conceded',
            'poss_won_att_3rd',
            'clean_sheet',
            '_save_percentage',
            'saves',
            '_goals_prevented',
            'goals_conceded',
            'fouls',
            'yellow_card',
            'red_card'
        ]

        self.team_possible_stats = ['rating_team',
            'goals_team_match',
            'goals_conceded_team_match',
            'possession_percentage_team',
            'clean_sheet_team',
            'expected_goals_team',
            'ontarget_scoring_att_team',
            'big_chance_team',
            'big_chance_missed_team',
            'accurate_pass_team',
            'accurate_long_balls_team',
            'accurate_cross_team',
            'penalty_won_team',
            'touches_in_opp_box_team',
            'corner_taken_team',
            'expected_goals_conceded_team',
            'interception_team',
            'won_tackle_team',
            'effective_clearance_team',
            'poss_won_att_3rd_team',
            'penalty_conceded_team',
            'saves_team',
            'fk_foul_lost_team',
            'total_yel_card_team',
            'total_red_card_team'
        ]
        
    def get_season_tables(self, league, season, table = ['all', 'home', 'away', 'form', 'xg']):
        leagues = get_possible_leagues_for_page(league, season, 'Fotmob')
        league_id = leagues[league]['id']
        season_string = season.replace('/', '%2F')
        response = requests.get(f'https://www.fotmob.com/api/leagues?id={league_id}&ccode3=ARG&season={season_string}')
        try:
            tables = response.json()['table'][0]['data']['table']
            table = tables[table]
            table_df = pd.DataFrame(table)
        except KeyError:
            tables = response.json()['table'][0]['data']['tables']
            table_df = tables
            print('This response has a list of two values, because the tables are split. If you save the list in a variable and then do variable[0]["table"] you will have all of the tables\nThen just select one ["all", "home", "away", "form", "xg"] that exists and put it inside a pd.DataFrame()\nSomething like pd.DataFrame(variable[0]["table"]["all"])')
        return table_df
    
    def request_match_details(self, match_id):
        response = requests.get(f'https://www.fotmob.com/api/matchDetails?matchId={match_id}')
        return response
    
    def get_players_stats_season(self, league, season, stat):
        print(f'Possible values for stat parameter: {self.player_possible_stats}')
        if stat not in self.player_possible_stats:
            raise InvalidStat(stat, self.player_possible_stats)
        leagues = get_possible_leagues_for_page(league, season, 'Fotmob')
        league_id = leagues[league]['id']
        season_id = leagues[league]['seasons'][season]
        response = requests.get(f'https://www.fotmob.com/api/leagueseasondeepstats?id={league_id}&season={season_id}&type=players&stat={stat}')
        time.sleep(1)
        df_1 = pd.DataFrame(response.json()['statsData'])
        df_2 = pd.DataFrame(response.json()['statsData']).statValue.apply(pd.Series)
        df = pd.concat([df_1, df_2], axis=1)
        return df
    
    def get_teams_stats_season(self, league, season, stat):
        print(f'Possible values for stat parameter: {self.team_possible_stats}')
        if stat not in self.team_possible_stats:
            raise InvalidStat(stat, self.team_possible_stats)
        leagues = get_possible_leagues_for_page(league, season, 'Fotmob')
        league_id = leagues[league]['id']
        season_id = leagues[league]['seasons'][season]
        response = requests.get(f'https://www.fotmob.com/api/leagueseasondeepstats?id={league_id}&season={season_id}&type=teams&stat={stat}')
        time.sleep(1)
        df_1 = pd.DataFrame(response.json()['statsData'])
        df_2 = pd.DataFrame(response.json()['statsData']).statValue.apply(pd.Series)
        df = pd.concat([df_1, df_2], axis=1)
        return df

    def get_match_shotmap(self, match_id):
        response = self.request_match_details(match_id)
        time.sleep(1)
        df_shotmap = pd.DataFrame(response.json()['content']['shotmap']['shots'])
        if df_shotmap.empty:
            raise MatchDoesntHaveInfo(match_id)
        ongoalshot = df_shotmap.onGoalShot.apply(pd.Series).rename(columns={'x': 'goalMouthY', 'y': 'goalMouthZ'}) 
        shotmap = pd.concat([df_shotmap, ongoalshot], axis=1).drop(columns=['onGoalShot'])
        return shotmap
    
    def get_team_colors(self, match_id):
        response = self.request_match_details(match_id)
        time.sleep(1)
        colors = response.json()['general']['teamColors']
        home_color = colors['darkMode']['home']
        away_color = colors['darkMode']['away']
        
        if home_color == '#ffffff':
            home_color = colors['lightMode']['home']
        if away_color == '#ffffff':
            away_color = colors['lightMode']['away']
        return home_color, away_color    
    
    def get_general_match_stats(self,match_id):
        response = self.request_match_details(match_id)
        time.sleep(1)
        total_df = pd.DataFrame()
        stats_df = response.json()['content']['stats']['Periods']['All']['stats']
        for i in range(len(stats_df)):
            df = pd.DataFrame(stats_df[i]['stats'])
            total_df = pd.concat([df, total_df])
        total_df = pd.concat([total_df, total_df.stats.apply(pd.Series).rename(columns={0: 'home', 1: 'away'})], axis=1) \
                .drop(columns=['stats']) \
                .dropna(subset=['home', 'away'])
        return total_df
    
    def get_player_shotmap(self, league, season, player_id):
        leagues = get_possible_leagues_for_page(league, season, 'Fotmob')
        league_id = leagues[league]['id']
        season_string = season.replace('/', '%2F')
        response = requests.get(f'https://www.fotmob.com/api/playerStats?playerId={player_id}&seasonId={season_string}-{league_id}')
        shotmap = pd.DataFrame(response.json()['shotmap'])
        return shotmap
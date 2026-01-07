import pandas as pd
import numpy as np
import seaborn as sns

def full_data_schedule_creation(start_year, end_year_noninc):
    for year in range(start_year, end_year_noninc):

        schedule = pd.read_csv(f"data/Schedules/{year}Games.csv")
        talent_comps = pd.read_csv(f"data/TalentComposites/{year}_Talent_Composite.csv")
        cohesion_stats = pd.read_csv(f"data/cohesion_stats/{year}.csv")

        hometalent_added = pd.merge(
            schedule, talent_comps[['Team', 'Talent']].rename(columns={'Team': 'HomeTeam'}),
            left_on="HomeTeam",
            right_on="HomeTeam",
            how='left'
        ).rename(columns={'Talent': 'HomeTeamTalent'})

        alltalent_added = pd.merge(
            hometalent_added, talent_comps[['Team', 'Talent']].rename(columns={'Team': 'AwayTeam'}),
            left_on="AwayTeam",
            right_on="AwayTeam",
            how='left'
        ).rename(columns={'Talent': 'AwayTeamTalent'})

        homeCohesion_added = pd.merge(
            alltalent_added, cohesion_stats[['Team', 'AverageScore']].rename(columns={'Team': 'HomeTeam'}),
            left_on="HomeTeam",
            right_on="HomeTeam",
            how='left'
        ).rename(columns={'AverageScore': 'HomeCohesionScore'})

        allCohesion_added = pd.merge(
            homeCohesion_added, cohesion_stats[['Team', 'AverageScore']].rename(columns={'Team': 'AwayTeam'}),
            left_on="AwayTeam",
            right_on="AwayTeam",
            how='left'
        ).rename(columns={'AverageScore': 'AwayCohesionScore'})

        def find_unexpected_results(row):
            HomeWin = False
            HomeMoreTalent = False
            unexpected_result = np.nan
            if row["HomePoints"] > row["AwayPoints"]:
                HomeWin = True
            if row["HomeTeamTalent"] > row["AwayTeamTalent"]:
                HomeMoreTalent = True
            if HomeWin != HomeMoreTalent:
                if HomeWin == True:
                    unexpected_result = 0
                else:
                    unexpected_result = 1
            return unexpected_result
            
        allCohesion_added['UnexpectedResult'] = allCohesion_added.apply(find_unexpected_results, axis = 1)

        final_col_order = ['Id', 'Season', 'Week', 'NeutralSite', 
                        'HomeId', 'HomeTeam', 'HomePoints', 'HomeTeamTalent', 'HomeCohesionScore', 
                        'AwayId', 'AwayTeam', 'AwayPoints', 'AwayTeamTalent', 'AwayCohesionScore',
                        'UnexpectedResult']

        fullData_schedule = allCohesion_added[final_col_order]



        fullData_schedule.to_csv(f"data/FullDataSchedules/{year}_FullDataSchedule.csv", index=False)

def full_data_analysis(start_year, end_year_noninc):
    all_years_data = []
    
    for year in range(start_year, end_year_noninc):
        cohesion_stats = pd.read_csv(f"data/cohesion_stats/{year}.csv")
        year_data = pd.read_csv(f"data/FullDataSchedules/{year}_FullDataSchedule.csv")
        
        unexpectedWins = {}
        for index, row in year_data.iterrows():
            if pd.notna(row["UnexpectedResult"]):
                homeTeam = row['HomeTeam']
                awayTeam = row['AwayTeam']
                if row["UnexpectedResult"] == 0:
                    try:
                        unexpectedWins[homeTeam] += 1
                    except KeyError:
                        unexpectedWins[homeTeam] = 1 
                else: 
                    try:
                        unexpectedWins[awayTeam] += 1
                    except KeyError:
                        unexpectedWins[awayTeam] = 1 
        # Build scatter plot data
        for team in unexpectedWins.keys():
            team_cohesion_row = cohesion_stats[cohesion_stats['Team'] == team]
            if not team_cohesion_row.empty:
                cohesion_score = team_cohesion_row['AverageScore'].values[0]
                all_years_data.append({
                    'Team': team,
                    'UnexpectedWins': unexpectedWins[team],
                    'CohesionScore': cohesion_score,
                    'Year': year
                })
    
    scatter_df = pd.DataFrame(all_years_data)
    return scatter_df


def plot_scatter_with_labels(scatter_df, save_path='plots'):
    """Create seaborn scatter plot with regression line and save to file"""
    import matplotlib.pyplot as plt
    from scipy import stats
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs(save_path, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter plot
    sns.scatterplot(data=scatter_df, x='CohesionScore', y='UnexpectedWins', 
                   s=50, alpha=0.6, ax=ax)
    
    # Add regression line with confidence interval
    sns.regplot(data=scatter_df, x='CohesionScore', y='UnexpectedWins', 
               scatter=False, ax=ax, line_kws={'color':'red', 'linewidth':2})
    
    # Calculate and display correlation
    corr, pval = stats.pearsonr(scatter_df['CohesionScore'], scatter_df['UnexpectedWins'])
    ax.text(0.05, 0.95, f'r={corr:.3f}\np={pval:.3f}', 
           transform=ax.transAxes, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax.set_xlabel('Cohesion Score')
    ax.set_ylabel('Unexpected Wins')
    ax.set_title('Team Cohesion vs Unexpected Wins')
    
    plt.tight_layout()
    
    # Save the figure
    output_file = os.path.join(save_path, 'cohesion_vs_unexpected_wins.png')
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Figure saved to {output_file}")
    
    plt.close(fig)
    return output_file





if __name__ == "__main__":
    full_data_schedule_creation(2020, 2026)
    scatter_df = full_data_analysis(2020, 2026)
    output_file = plot_scatter_with_labels(scatter_df)
    print(f"Plot successfully saved!")
"""
Module: scraper.py
Description: Contains functions to scrape event data (e.g., Sparta Praha match schedules)
             from external websites.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging


def scrape_sparta_matches(output_file: str = "data/sparta_matches.csv") -> pd.DataFrame:
    """
    Scrape Sparta Praha match schedule from the Eurofotbal website and save the data as a CSV.

    Parameters:
        output_file (str): Path to save the scraped CSV file. Defaults to "sparta_matches.csv".

    Returns:
        pd.DataFrame: A DataFrame containing match details.
    """
    url = "https://www.eurofotbal.cz/kluby/cesko/sparta-praha/zapasy/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        match_rows = soup.find_all("div", class_="e-tables-table-overview__row")
        matches = []
        for row in match_rows:
            # Extract competition and round details.
            competition_cell = row.find("div", class_="e-tables-table-overview__cell--league")
            competition = competition_cell.text.strip() if competition_cell else ""
            round_cell = row.find("div", class_="e-tables-table-overview__cell--round")
            round_text = round_cell.text.strip() if round_cell else ""
            
            # Extract date and time details.
            date_cells = row.find_all("div", class_="e-tables-table-overview__cell--gray")
            if len(date_cells) >= 4:
                date_str = date_cells[2].text.strip()
                time_str = date_cells[3].text.strip()
            else:
                date_str, time_str = "", ""
            
            # Extract team names.
            team_cells = row.find_all("div", class_="e-tables-table-overview__result-team-label")
            home_team = team_cells[0].text.strip() if team_cells and len(team_cells) > 0 else ""
            away_team = team_cells[1].text.strip() if team_cells and len(team_cells) > 1 else ""
            
            # Determine match location and opponent.
            if home_team == "Sparta Praha":
                is_home = True
                opponent = away_team
                location = "D"
            elif away_team == "Sparta Praha":
                is_home = False
                opponent = home_team
                location = "V"
            else:
                is_home = None
                opponent = "Unknown"
                location = "Neutral"
            
            # Extract the match score.
            score_cell = row.find("span", class_="e-tables-table-overview__result-score-inner")
            score = score_cell.text.strip() if score_cell else "- : -"
            
            match_data = {
                "Home Team": home_team,
                "Away Team": away_team,
                "Opponent": opponent,
                "is_home": is_home,
                "Competition": competition,
                "Round": round_text,
                "Date": date_str,
                "Time": time_str,
                "Score": score,
                "Location": location,
                "datetime": f"{date_str} {time_str}"
            }
            matches.append(match_data)
        
        df = pd.DataFrame(matches)
        df.to_csv(output_file, index=False)
        logging.info(f"Matches saved to {output_file}")
        return df
    except Exception as e:
        logging.error(f"Error scraping match data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

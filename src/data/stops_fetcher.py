"""
Module: stops_fetcher.py
Description: Contains the StopsFetcher class to retrieve stops data from the Golemio API.
"""

import os
import requests
import pandas as pd
import logging


class StopsFetcher:
    """
    A class to fetch stops data from the Golemio API.
    """

    def __init__(self, base_url: str = "https://api.golemio.cz/v2/gtfs/stops") -> None:
        """
        Initialize the StopsFetcher with a base URL and default stop names.

        Parameters:
            base_url (str): The API endpoint to fetch stops data.
        """
        self.base_url = base_url
        self.stop_names = [
            "Hradčanská",
            "Sparta",
            "Korunovační",
            "Letenské náměstí",
            "Kamenická",
            "Strossmayerovo náměstí",
            "Nábřeží Kapitána Jaroše",
            "Vltavská",
            "Výstaviště",
            "Veletržní palác"
        ]
        self.token = os.getenv("X-Access-Token-Golemio")
        if not self.token:
            logging.warning("X-Access-Token-Golemio environment variable not set.")

    def fetch_stops(self) -> dict:
        """
        Fetch stops data from the Golemio API.

        Returns:
            dict: The JSON response from the API.
        """
        params = {"names[]": self.stop_names, "offset": 0}
        headers = {"accept": "application/json", "X-Access-Token": self.token}
        try:
            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching stops: {e}")
            return {}

    def process_stops(self) -> pd.DataFrame:
        """
        Process the fetched stops JSON into a pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame with columns: gtfs_stop_id, stop_name, and coordinates.
        """
        stops_json = self.fetch_stops()
        stops_list = []
        for feature in stops_json.get("features", []):
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", None)
            stop_id = properties.get("gtfs_stop_id", properties.get("stop_id"))
            stop_name = properties.get("stop_name")
            if stop_id and stop_name and coordinates:
                stops_list.append({
                    "gtfs_stop_id": stop_id,
                    "stop_name": stop_name,
                    "coordinates": coordinates
                })
        return pd.DataFrame(stops_list)

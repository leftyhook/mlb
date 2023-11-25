"""
Tools for retrieving data from fangraphs.com.

Disclaimer:
    The author of this source code is not affiliated with www.fangraphs.com in any way.
    The use of www.fangraphs.com is subject to any terms and conditions posted on www.fangraphs.com.
"""
import logging
import requests

from requests.compat import urljoin
from io import StringIO
from pandas import DataFrame, read_html

from mlb.statsapi.statsapi import current_mlb_season

URL = "https://www.fangraphs.com"


class FanGraphsGuts:
    """Class that goes out to the fangraphs guts page and can extract any of the tables included there."""
    def __init__(self):
        self.url = urljoin(URL, "/guts.aspx")

    def _get_table(self, params: dict) -> DataFrame:
        """
        Sends an HTTP request to fangraphs guts and extracts the data table included in the HTML response.

        Parameters:
            params (dict): A dictionary of url params to include in the HTTP request.
        Returns:
            pandas.DataFrame: The HTML table converted to a pandas DataFrame.
        """
        resp = requests.get(self.url, params)
        if resp.status_code == 200:
            tables = read_html(StringIO(resp.text), attrs={"class": "rgMasterTable"})
            return tables[len(tables) - 1]
        else:
            resp.raise_for_status()

    def get_woba_and_fip_constants(self) -> DataFrame:
        """Returns the 'WOBA and FIP constants' table from fangraphs guts, as a dataframe."""
        return self._get_table(params={"type": "cn"})

    def get_park_factors(self, season: int = current_mlb_season()) -> DataFrame:
        """
        Returns the 'Park Factors' table from fangraphs guts, as a dataframe.

        Parameters:
            season (int): Optional. The year of the MLB season. Defaults to the current season.
        """
        return self._get_table(
            params={"type": "pf", "teamid": "0", "season": season}
        )

    def get_handedness_park_factors(
        self, season: int = current_mlb_season()
    ) -> DataFrame:
        """
        Returns the 'Handedness Park Factors' table from fangraphs guts, as a dataframe.

        Parameters:
            season (int): Optional. The year of the MLB season. Defaults to the current season.
        """
        return self._get_table(
            params={"type": "pfh", "teamid": "0", "season": season}
        )


def download_woba_and_fip_constants(file_path: str):
    """
    Download WOBA and FIP constants from fangraphs guts to a file.

    Parameters:
        file_path (str): The path to the file to write.
    """
    fg = FanGraphsGuts()
    logging.info("Getting WOBA and FIP constants from %s" % URL)
    df = fg.get_woba_and_fip_constants()
    df.to_csv(file_path, index=False)
    logging.info("Fangraphs WOBA and FIP constants written to %s" % file_path)

# mlb.statcast

A package for automating retrieval of downloadable [statcast](https://www.mlb.com/glossary/statcast) data from 
baseballsavant.mlb.com.

## statcast_search.py

baseballsavant.mlb.com is a veritable gold mine of MLB statistical data. Their 
[Statcast Search](https://baseballsavant.mlb.com/statcast_search) page offers endless ways to query that data, and the 
site generously allows users to download their query results.

[statcast_search.py](https://github.com/leftyhook/mlb/blob/main/mlb/statcast/statcast_search.py) provides a flexible 
(albeit intentionally limited) interface - the __StatcastSearch__ class - to build, execute, and return the results of 
statcast searches. It also provides functions that wrap common searches.  

Developers can easily extend statcast_search.py to support additional search use cases by adding new parameter classes 
or search wrapper functions.

#### Notes

* The maximum number of rows baseballsavant allows to be downloaded at one time is 25,000.

## pitch_data.py

One of the great features of the Statcast Search web page is that it allows users to download the pitch data that serves
as the back end to their search queries. The data points included are too many to list here, but among the most
interesting are:
- The type of pitch thrown.
- Velocity, spin rate, and location measurements of each pitch.
- Exit velocities and launch angles of batted balls.
- Information on the game state (number of outs, runners on base, who the defensive players are, etc.) at the time of the pitch.
- [Expected statistics](https://baseballsavant.mlb.com/leaderboard/expected_statistics), 
calculated by MLB and based on the historical outcomes of comparable batted balls.

*This data is available for every pitch thrown in every MLB game!* It provides endless opportunities for users to perform
their own statistical analysis.

### PitchDataDownloadManager

Retrieving pitch data is one of the core functions of the statcast package. In a likely use case, a user might wish to
retrieve all pitch data for an entire MLB season. They may wish to retroactively backfill all the data for a prior
season, or retrieve new data daily throughout the current season as it becomes available. In either case, pitch_data.py
provides the __PitchDataDownloadManager__ class to achieve the goal by taking the following into consideration:
* Out of respect to the data provider, we wish to execute the smallest possible number of HTTP requests to Statcast Search.
* Over 700,000 pitches will be thrown in a typical MLB season, but Baseball Savant only allows us to download up to 
25,000 at one time.
* For pitches that do not result in a ball being hit into play, the data is static. In the ideal scenario, that data
would be downloaded exactly once and stored on the local file system for future use.
* For pitches that result in batted ball events, the values of the calculated 'expected' statistics will change as the
season progresses and more batted ball events are recorded for comparison. Once the season is complete, that data also
becomes static. (Note: A user could download batted ball data once and then perform their own version of the calculation 
described at https://technology.mlblogs.com/an-introduction-to-expected-weighted-on-base-average-xwoba-29d6070ba52b
to compute 'expected' statistics, but we assume the user will want to rely on MLB's calculation and will need to 
refresh this data daily throughout the season to get the most accurate values).

PitchDataDownloadManager will organize and execute the optimal number of searches to produce a complete set of 
up-to-date pitch data for a given time period. The resulting output will be current versions of the following files:
1. One file of non-batted ball event ("NonBBE") data for every date in the date range.
2. A single cumulative file of batted ball event ("BBE") data.

### SeasonPitchData

Taking it one step further, pitch_data.py also provides the __SeasonPitchData__ class, which leverages 
PitchDataDownloadManager to retrieve the pitch data for a given MLB season and present it in a single file.

#### Notes

- *Be aware of how much data is being downloaded!* The pitch data for an entire season will require **approximately 370
megabytes** of disk space. The SeasonPitchData class **doubles** this output by combining the data from every day's 
NonBBE file along with the BBE data into a single file.

## Usage

* For the best example of how to use the statcast package to download pitch data, see the 
[pitch_data_harvester](https://github.com/leftyhook/mlb/blob/main/scripts/pitch_data_harvester.py) script.
* The [pitch_data_demo](https://github.com/leftyhook/mlb/blob/main/mlb/pitch_data_demo) shows the pitch_data_harvester 
script in action.

<br/>

### Disclaimer:

The author of this source code is not affiliated with Major League Baseball in any way.
The use of baseballsavant.mlb.com is subject to any terms and conditions posted on baseballsavant.mlb.com.
# mlb.scripts

Scripts incorporating the components of the mlb package. 

## Config

The [mlb_config.py](https://github.com/leftyhook/mlb/blob/main/mlb/scripts/mlb_config.py) module loads an ini config 
file into a custom Python object, intended for use by any scripts in this package that require more sophisticated 
configuration than can reasonably be performed at the command line.

The module's **Config** class will recognize the following sections and keys:

| Section | Key                 | Description                                                                                                                         |
| ------- |---------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| DIRS    | pitch_data          | The directory to read pitch data from and wirte it to                                                                               |
| PATHS   | fangraphs_constants | The full file path to a file storing a table of fangraphs' FIP & wOBA constants                                                     | 
| PATHS   | woba_constants      | The full file path to a file storing a table of FIP and wOBA constants. Can (and usually should be) the same as fangraphs_constants |                    

#### Notes

* If creating your own config, note that the config parser uses
[Extended Interpolation](https://docs.python.org/3/library/configparser.html#configparser.ExtendedInterpolation) to 
handle interpolation of values.
* See the [sample_config.ini](https://github.com/leftyhook/mlb/blob/main/sample_config.ini) for an example of a valid 
config with interpolated values.

---

## pitch_data_harvester.py

A script for harvesting MLB pitch data for a given season and writing it to file.

### Supported Python Versions

Python 3.9 and above

### Usage

    usage: pitch_data_harvester.py [-h] -c CONFIG [-s SEASON] [-g {S,R,F,D,L,W}] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                                   [-f LOG_FILE]
    
    options:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            Full file path to ini config file.
      -s SEASON, --season SEASON
                            MLB season
      -g {S,R,F,D,L,W}, --game-type-code {S,R,F,D,L,W}
                            The statsapi single-character code representing the game type.
                            S=Preseason 
                            R=Regular 
                            F=Wildcard 
                            D=DivisionSeries 
                            L=LeagueChampionshipSeries 
                            W=WorldSeries
      -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            Log level. Defaults to DEBUG
      -f LOG_FILE, --log-file LOG_FILE
                            Log file. If provided, the file name will be amended to include today's date. If omitted,
                            logging will still write to stdout.

### Config

The ini config requires the following section and key content as described in the Config section above:

| Section | Key                 |
| ------- |---------------------|
| DIRS    | pitch_data          |
| PATHS   | fangraphs_constants |
| PATHS   | woba_constants      |



### Output
Upon successful execution, the script will generate any of the following that do not already exist, or update any that
do exist, if necessary:
1. One file of non-batted ball event ("NonBBE") data for every game date in the season.
2. A single cumulative file of batted ball event ("BBE") data.
3. A single master file containing all pitch data for the entire season.
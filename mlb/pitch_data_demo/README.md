# mlb.pitch_data_demo

Demonstrating how to use 
[pitch_data_harvester.py](https://github.com/leftyhook/mlb/blob/main/mlb/scripts/pitch_data_harvester.py) to download all 
pitch data for a season.

It will download the pitch data for the 2023 World Series directly into the pitch_data_demo directory.

## Supported Architectures

- Windows 10 and above

## Supported Python Versions

- Python 3.9 and above

## Run

1. [Install](https://github.com/leftyhook/mlb/tree/main#install) the mlb package.
2. From a command prompt, change the working directory to \<package installation location>\mlb\pitch_data_demo.
3. On the command line, type ```run_demo.bat``` and press Enter!

## Output
pitch_data_harvester will log to the console as the script runs. Upon completion, the following files will have been 
created in your pitch_data_demo directory (total size approximately 1.5 megabytes):

    FanGraphs.wOBA_and_FIP_Constants.csv
    PitchData.2023.WorldSeries.csv
    PitchData.BBE.2023.WorldSeries.csv
    PitchData.NonBBE.2023-10-27.csv
    PitchData.NonBBE.2023-10-28.csv
    PitchData.NonBBE.2023-10-30.csv
    PitchData.NonBBE.2023-10-31.csv
    PitchData.NonBBE.2023-11-01.csv
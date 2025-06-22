# mlb

Python applications for acquiring publicly available Major League Baseball data and statistics for analysis and modeling.

## Supported Python Versions

Python 3.9 and above

## Build

- This project is configured to use [build](https://pypi.org/project/build/) with [setuptools](https://setuptools.pypa.io/en/latest/setuptools.html).
- From the project root directory, run:
    ```commandline
    python -m build
    ```
- This will generate a new wheel file in /dist subdirectory of root. Note the name of the file for the installation step.

## Install

- The package can be installed from the new wheel file with [pip](https://pypi.org/project/pip/).
- From the /dist subdirectory, run either of the following commands (replacing items in \<> with the appropriate 
values) according to where you want to install the package. 
  - To install to the default location (your Python version's site-packages directory): 
    ```commandline
    python -m pip install <wheel filename>
    ```
  - To install to a custom directory:
    ```commandline
    python -m pip install <wheel filename> --target=<directory>
    ```

## Run

- See the [scripts](https://github.com/leftyhook/mlb/blob/main/mlb/scripts) directory for packaged scripts
- Or try the [pitch data demo](https://github.com/leftyhook/mlb/blob/main/mlb/pitch_data_demo)!

&nbsp; 

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/leftyhook/mlb/blob/main/LICENSE.txt)
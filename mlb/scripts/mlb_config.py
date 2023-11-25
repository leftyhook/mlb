"""
Class module to read a config file and generate a custom configuration object with
attributes that specify common settings required by other modules in this project.
"""
import configparser

from os import path


class Config:
    def __init__(self, file_path: str):
        parser = configparser.SafeConfigParser(interpolation=configparser.ExtendedInterpolation())

        if not path.exists(file_path):
            raise FileNotFoundError(f"Config file {file_path} not found.")

        parser.read(file_path)
        section_dirs = parser["DIRS"]
        section_paths = parser["PATHS"]

        self.pitch_data_dir = path.expandvars(section_dirs.get("pitch_data", ""))
        self.woba_const_file_path = path.expandvars(section_paths.get("woba_constants", ""))
        self.fangraphs_const_file_path = path.expandvars(section_paths.get("fangraphs_constants", ""))

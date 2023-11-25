import sys
import argparse
import datetime
import logging
import logging.config

from mlb.scripts.mlb_config import Config
from mlb.utils.file_utils import add_date_to_file_name
from mlb.statsapi import statsapi
from mlb.stats import woba
from mlb.statcast.pitch_data import SeasonPitchData

DEFAULT_LOG_LEVEL_STDOUT = 'DEBUG'
DEFAULT_LOG_LEVEL_FILE = 'INFO'

logger = logging.getLogger()


def configure_logging(log_level: str, log_file: str = None):
    """
    Configure the logging for the session.

    Logging will always occur to stdout with this configuration.
    If no log file is provided, stdout logging level will be set to log_level.
    If a file is provided, stdout logging will proceed at its default level,
    and a file log handler will be added at log_level.

    Parameters:
        log_level (str): The string value of a logging.Level.
        log_file (str): Optional. The file to write log output to. Defaults to None.
    """
    config = {
        'version': 1,
        'filters': {},
        'formatters': {
            'formatter': {
                'format': '%(asctime)s::%(levelname)s::%(module)s::%(funcName)s()::%(lineno)d::%(message)s'
            }
        },
        'handlers': {
            'console_stdout': {
                'class': 'logging.StreamHandler',
                'level': log_level if not log_file else DEFAULT_LOG_LEVEL_STDOUT,
                'formatter': 'formatter',
                'stream': sys.stdout
            },
        },
        'root': {
            'level': 'NOTSET',
            'handlers': ['console_stdout']
        },
    }

    if log_file:
        today = datetime.date.today()
        log_file = add_date_to_file_name(log_file, today, "%Y%m%d")

        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": log_level,
            "formatter": "formatter",
            "filename": log_file,
            "encoding": "utf8"
        }
        config["root"]["handlers"].append("file")

    logging.config.dictConfig(config)


def parse_args(args: list) -> argparse.Namespace:
    """
    Parse a list of command line arguments.

    Parameters:
        args (list): The list of command line arguments

    Returns:
        argparse.Namespace: The parsed arguments
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="Full file path to ini config file.",
    )
    arg_parser.add_argument(
        "-s",
        "--season",
        type=int,
        required=False,
        default=statsapi.current_mlb_season(),
        help="MLB season",
    )
    arg_parser.add_argument(
        "-g",
        "--game-type-code",
        type=str,
        required=False,
        choices=[
            statsapi.GAME_TYPE_CODE_PRESEASON,
            statsapi.GAME_TYPE_CODE_REGULAR,
            statsapi.GAME_TYPE_CODE_WILDCARD,
            statsapi.GAME_TYPE_CODE_DIV_SERIES,
            statsapi.GAME_TYPE_CODE_LCS,
            statsapi.GAME_TYPE_CODE_WS,
        ],
        default=statsapi.GAME_TYPE_CODE_REGULAR,
        help=(
            "The statsapi single-character code representing the game type.\n"
            f"{statsapi.GAME_TYPE_CODE_PRESEASON}={statsapi.game_type_str(statsapi.GAME_TYPE_CODE_PRESEASON)}\n"
            f"{statsapi.GAME_TYPE_CODE_REGULAR}={statsapi.game_type_str(statsapi.GAME_TYPE_CODE_REGULAR)}\n"
            f"{statsapi.GAME_TYPE_CODE_WILDCARD}={statsapi.game_type_str(statsapi.GAME_TYPE_CODE_WILDCARD)}\n"
            f"{statsapi.GAME_TYPE_CODE_DIV_SERIES}={statsapi.game_type_str(statsapi.GAME_TYPE_CODE_DIV_SERIES)}\n"
            f"{statsapi.GAME_TYPE_CODE_LCS}={statsapi.game_type_str(statsapi.GAME_TYPE_CODE_LCS)}\n"
            f"{statsapi.GAME_TYPE_CODE_WS}={statsapi.game_type_str(statsapi.GAME_TYPE_CODE_WS)}\n"
        )
    )
    arg_parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        required=False,
        default=DEFAULT_LOG_LEVEL_STDOUT,
        choices=[
            logging.getLevelName(logging.DEBUG),
            logging.getLevelName(logging.INFO),
            logging.getLevelName(logging.WARNING),
            logging.getLevelName(logging.ERROR),
            logging.getLevelName(logging.CRITICAL)
        ],
        help=f"Log level. Defaults to {DEFAULT_LOG_LEVEL_STDOUT}",
    ),
    arg_parser.add_argument(
        "-f",
        "--log-file",
        type=str,
        required=False,
        default=None,
        help=("Log file. If provided, the file name will be amended to include today's date. "
              "If omitted, logging will still write to stdout.")
    )
    return arg_parser.parse_args(args)


def main(cmd_line_args: list):
    """
    Main program. Refreshes downloaded pitch data from statcast for a given MLB season.

    Parameters:
        cmd_line_args (list): List of command line arguments
    """
    try:
        parsed_args = parse_args(cmd_line_args)

        configure_logging(parsed_args.log_level, parsed_args.log_file)
        logging.info("Running Python version %s" % sys.version)
        logger.info(
            "pitch_data_harvester started with command line arguments: %s" % str(cmd_line_args)
        )

        config = Config(parsed_args.config)
        pitch_data_file = SeasonPitchData(
            parsed_args.season,
            parsed_args.game_type_code,
            config.pitch_data_dir
        )

        woba_const_history = woba.WOBAConstantHistory.load_from_file(
            file_path=config.woba_const_file_path,
            stale_by_date=pitch_data_file.stale_by_date,
            use_fangraphs=(config.fangraphs_const_file_path == config.woba_const_file_path)
        )

        pitch_data_file.refresh(woba_const_history)
        logging.info("Process complete. Exiting.")
    except Exception as exc:
        logging.exception(exc)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])

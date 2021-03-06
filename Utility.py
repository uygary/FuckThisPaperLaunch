from datetime import datetime
from distutils.util import strtobool
import os


class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Utility:

    @staticmethod
    def timestamp_log_message(log_message):
        return f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}::{log_message}"

    @staticmethod
    def log_verbose(log_message):
        print(f"{TerminalColors.OKBLUE}{Utility.timestamp_log_message(log_message)}{TerminalColors.ENDC}")

    @staticmethod
    def log_information(log_message):
        print(f"{TerminalColors.OKGREEN}{Utility.timestamp_log_message(log_message)}{TerminalColors.ENDC}")

    @staticmethod
    def log_warning(log_message):
        print(f"{TerminalColors.WARNING}{Utility.timestamp_log_message(log_message)}{TerminalColors.ENDC}")

    @staticmethod
    def log_error(log_message):
        print(f"{TerminalColors.FAIL}{Utility.timestamp_log_message(log_message)}{TerminalColors.ENDC}")

    @staticmethod
    def parse_price_string(price_string):
        cleaned_price_string = price_string \
            .replace(",", "") \
            .replace("$", "") \
            .replace("£", "") \
            .replace("€", "")
        parsed_price = float(cleaned_price_string)

        return parsed_price

    @staticmethod
    def beep():
        print("\a")

    @staticmethod
    def get_config_value_str(config_key):
        return os.environ.get(config_key)

    @staticmethod
    def get_config_value_int(config_key):
        return int(os.environ.get(config_key))

    @staticmethod
    def get_config_value_float(config_key):
        return float(os.environ.get(config_key))

    @staticmethod
    def get_config_value_bool(config_key):
        return bool(strtobool(os.environ.get(config_key)))
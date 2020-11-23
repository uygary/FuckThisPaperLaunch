from datetime import datetime


class Utility:

    @staticmethod
    def timestamp_log_message(log_message):
        return f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}::{log_message}"

    @staticmethod
    def log_verbose(log_message):
        print(Utility.timestamp_log_message(log_message))

    @staticmethod
    def log_information(log_message):
        print(Utility.timestamp_log_message(log_message))

    @staticmethod
    def log_warning(log_message):
        print(Utility.timestamp_log_message(log_message))

    @staticmethod
    def log_error(log_message):
        print(Utility.timestamp_log_message(log_message))

    @staticmethod
    def parse_price_string(price_string):
        cleaned_price_string = price_string \
            .replace(",", "") \
            .replace("$", "") \
            .replace("£", "") \
            .replace("€", "")
        parsed_price = float(cleaned_price_string)

        return parsed_price

import datetime
import dateparser
from typing import Optional
class DatetimeUtils:

    @staticmethod
    def try_parse_datetime(date_string: str) -> Optional[datetime.datetime]:
        return dateparser.parse(date_string, languages=["vi", "en", "zh", "de", "fr", "ru"])

    @staticmethod
    def from_timestamp(timestamp: int) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(timestamp)
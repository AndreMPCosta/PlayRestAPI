import time
from datetime import datetime


def str_to_time(time_string):
    return datetime.strptime(time_string, '%H:%M:%S').time()


def convert_date(date):
    return datetime.strptime(date, "%d-%m-%Y")


if __name__ == "__main__":
    print(str_to_time("19:20:00"))
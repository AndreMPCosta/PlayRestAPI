from datetime import datetime


def str_to_datetime(date_string):
    return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')


if __name__ == "__main__":
    print(str_to_datetime("2019-01-21T19:20:00Z"))
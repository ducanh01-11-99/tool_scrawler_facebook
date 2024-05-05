import time
import socket
import calendar
from datetime import datetime, timedelta

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def write_data_to_file(path_file, message, mode = "a"):
    with open(path_file, mode, encoding="utf-8") as fp:
        fp.write(message)
        fp.write("\n")


def read_data_from_file(path_file, mode = "r"):
    lines = []
    with open(path_file, mode, encoding="utf-8") as fp:
        for line in fp:
            lines.append(line)

    return lines

def normalizationDateTime(text):
    if (text.find("January") != -1):
        text = text.replace("January", "Jan")
    if (text.find("February") != -1):
        text = text.replace("February", "Feb")
    if (text.find("") != -1):
        text = text.replace("March", "Mar")
    if (text.find("April") != -1):
        text = text.replace("April", "Apr")
    if (text.find("May") != -1):
        text = text.replace("May", "May")
    if (text.find("June") != -1):
        text = text.replace("June", "Jun")
    if (text.find("July") != -1):
        text = text.replace("July", "Jul")
    if (text.find("August") != -1):
        text = text.replace("August", "Aug")
    if (text.find("September") != -1):
        text = text.replace("September", "Sep")
    if (text.find("October") != -1):
        text = text.replace("October", "Oct")
    if (text.find("November") != -1):
        text = text.replace("November", "Nov")
    if (text.find("December") != -1):
        text = text.replace("December", "Dec")

    if len(text) <= 3:
        text = text.replace("m", " min")
        text = text.replace("h", " hour")
        text = text.replace("d", " day")
    return text

def GetOldTime(distance_milis_time):
    time_now = time.strftime("%m/%d/%Y %H:%M:%S", time.gmtime())
    timestamp_now = calendar.timegm(
        time.strptime(time_now, "%m/%d/%Y %H:%M:%S"))
    dt_object = datetime.fromtimestamp(timestamp_now - distance_milis_time)
    return dt_object.strftime("%m/%d/%Y %H:%M:%S")

def get_create_time(text):
    # x hrs | x mins | hr | min | h | m
    # August 13, 2018 at 3:24 PM | August 13 at 12:23 AM | February 14, 2017 at 12:35 PM
    # July 27, 2018 at 1:19 AM  | October 24, 2016 at 12:39 PM | 9 hrs · Public
    # August 15 at 11:35 PM · Public | Yesterday at 8:39 AM · Public | August 15 · Public

    # 4 minutes ago | Just now |x hrs | x mins | hr | min

    text = normalizationDateTime(text)

    time_now = GetOldTime(0)
    dateTimeNow = datetime.now()

    # July 10
    if text.find("at") == -1 and text.find("hour") == -1 and text.find("hr") == -1 and text.find(
            "min") == -1 and text.find("Just now") == -1 and text.find("day") == -1:
        month = '00'
        if (text.find("Jan") != -1):
            month = '01'
        if (text.find("Feb") != -1):
            month = '02'
        if (text.find("Mar") != -1):
            month = '03'
        if (text.find("Apr") != -1):
            month = '04'
        if (text.find("May") != -1):
            month = '05'
        if (text.find("Jun") != -1):
            month = '06'
        if (text.find("Jul") != -1):
            month = '07'
        if (text.find("Aug") != -1):
            month = '08'
        if (text.find("Sep") != -1):
            month = '09'
        if (text.find("Oct") != -1):
            month = '10'
        if (text.find("Nov") != -1):
            month = '11'
        if (text.find("Dec") != -1):
            month = '12'
        #
        if month != '00':
            day = text.split(" ")[1]
            if day.isdecimal():
                if int(day) <= 9:
                    day = '0' + day
                #
                created_time = month + "/" + day + \
                               "/2021 " + time.strftime("%H:%M:%S", time.gmtime())
                return created_time, 30

    if (text.find("Just now") != -1):
        created_time = time_now
        return created_time, 0

    if (text.find("min") != -1):
        minutes = text.split(" min")[0]
        if (minutes.isdecimal()):
            created_time = GetOldTime(60 * int(minutes))
            return created_time, 0
        else:
            return time_now, 0

    if (text.find("hr") != -1):
        hr = text.split(" hr")[0]
        if (hr.isdecimal()):
            created_time = GetOldTime(60 * 60 * int(hr))
            return created_time, 0
        else:
            return time_now, 0

    if (text.find("hour") != -1):
        hr = text.split(" hour")[0]
        if (hr.isdecimal()):
            created_time = GetOldTime(60 * 60 * int(hr))
            return created_time, 0
        else:
            return time_now, 0

    if (text.find("day") != -1):
        day = text.split(" day")[0]
        if (day.isdecimal()):
            created_time = GetOldTime(60 * 60 * 24 * int(day))
            return created_time, int(day)
        else:
            return time_now, 0
    # Yesterday at 8:39 AM
    if (text.find("Yesterday") != -1 and text.find("at") != -1):
        hr = text.split("at ")[1].split(":")[0]
        mins = text.split("at ")[1].split(":")[1].split(" ")[0]
        if text.find("PM") != -1:
            hr = int(hr) + 11
            hr = str(hr)
        if int(hr) <= 9:
            hr = "0" + hr
        #
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        created_time = f'{yesterday:%m/%d/%Y}'
        created_time += " " + hr + ":" + mins + ":01"
        return created_time, 1

    # Today at 8:39 AM
    if (text.find("Today") != -1 and text.find("at") != -1):
        hr = text.split("at ")[1].split(":")[0]
        mins = text.split("at ")[1].split(":")[1].split(" ")[0]
        if text.find("PM") != -1:
            hr = int(hr) + 11
            hr = str(hr)
        if int(hr) <= 9:
            hr = "0" + hr
        #
        now = datetime.now()
        created_time = f'{now:%m/%d/%Y}'
        created_time += " " + hr + ":" + mins + ":01"
        return created_time, 1

    # Saturday at 8:39 AM
    if (text.find("at") != -1):
        if (text.find("Mon") != -1 or text.find("Tue") != -1 or text.find("Wed") != -1 or text.find(
                "Thu") != -1 or text.find("Fri") != -1 or text.find("Sat") != -1 or text.find("Sun") != -1):
            hr = text.split("at ")[1].split(":")[0]
            mins = text.split("at ")[1].split(":")[1].split(" ")[0]
            if text.find("PM") != -1:
                hr = int(hr) + 11
                hr = str(hr)
            if int(hr) <= 9:
                hr = "0" + hr
            #
            now = datetime.now()
            yesterday = now - timedelta(days=4)
            created_time = f'{yesterday:%m/%d/%Y}'
            created_time += " " + hr + ":" + mins + ":01"
            return created_time, 3

    # July 27, 2018 at 1:19 AM | July 27 at 1:19 AM
    if ((text.find("AM") != -1 or text.find("PM") != -1) and text.find("at") != -1):
        if text.find(",") != -1:
            date = text.split(' ')[1].split(',')[0]
            year = text.split(' ')[2]
        else:
            date = text.split(' ')[1].split(' ')[0]
            year = '2021'
        #
        month = '01'
        if (text.find("Jan") != -1):
            month = '01'
        if (text.find("Feb") != -1):
            month = '02'
        if (text.find("Mar") != -1):
            month = '03'
        if (text.find("Apr") != -1):
            month = '04'
        if (text.find("May") != -1):
            month = '05'
        if (text.find("Jun") != -1):
            month = '06'
        if (text.find("Jul") != -1):
            month = '07'
        if (text.find("Aug") != -1):
            month = '08'
        if (text.find("Sep") != -1):
            month = '09'
        if (text.find("Oct") != -1):
            month = '10'
        if (text.find("Nov") != -1):
            month = '11'
        if (text.find("Dec") != -1):
            month = '12'

        if text.find("at") != -1:
            hr = text.split("at ")[1].split(":")[0]
            mins = text.split("at ")[1].split(":")[1].split(" ")[0]
            if text.find("PM") != -1:
                hr = int(hr) + 11
                hr = str(hr)
            if int(hr) <= 9:
                hr = "0" + hr
            if int(date) <= 9:
                date = "0" + date
            created_time = month + "/" + date + "/" + year + " " + hr + ":" + mins + ":01"
            dateTimePost = datetime.strptime(created_time, "%m/%d/%Y %H:%M:%S")
            dateTimeDifference = dateTimeNow - dateTimePost
            distance_time = dateTimeDifference.total_seconds() / (3600 * 24)
            return created_time, distance_time
        else:
            if int(month) <= 9:
                month = "0" + month
            if int(date) <= 9:
                date = "0" + date
            created_time = month + "/" + date + "/" + year + " " + "09:43:23"
            dateTimePost = datetime.strptime(created_time, "%m/%d/%Y %H:%M:%S")
            dateTimeDifference = dateTimeNow - dateTimePost
            distance_time = dateTimeDifference.total_seconds() / (3600 * 24)
            return created_time, distance_time
    # July 27, 2018
    if text.find(",") != -1:
        date = text.split(' ')[1].split(',')[0]
        year = text.split(' ')[2]
        #
        month = '01'
        if (text.find("Jan") != -1):
            month = '01'
        if (text.find("Feb") != -1):
            month = '02'
        if (text.find("Mar") != -1):
            month = '03'
        if (text.find("Apr") != -1):
            month = '04'
        if (text.find("May") != -1):
            month = '05'
        if (text.find("Jun") != -1):
            month = '06'
        if (text.find("Jul") != -1):
            month = '07'
        if (text.find("Aug") != -1):
            month = '08'
        if (text.find("Sep") != -1):
            month = '09'
        if (text.find("Oct") != -1):
            month = '10'
        if (text.find("Nov") != -1):
            month = '11'
        if (text.find("Dec") != -1):
            month = '12'
        if int(month) <= 9 and len(month) == 1:
            month = "0" + month
        if int(date) <= 9 and len(date) == 1:
            date = "0" + date
        created_time = month + "/" + date + "/" + year + " " + "09:43:23"
        dateTimePost = datetime.strptime(created_time, "%m/%d/%Y %H:%M:%S")
        dateTimeDifference = dateTimeNow - dateTimePost
        distance_time = dateTimeDifference.total_seconds() / (3600 * 24)
        return created_time, distance_time
    return time_now, 0
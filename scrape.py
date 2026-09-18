from datetime import date, timedelta, datetime, time
import time as tm
import pandas as pd
import numpy as np
import requests

URL_TEMPLATE = "https://br.so-ups.ru/webapi/api/map/MapPartial?MapType=0&Date={date}&Hour={hour}&PowerSystemId=630000&SubjectId=75&ServiceMode=false"


def download_data(date,time):
    url = URL_TEMPLATE.format(date=date,hour=time)
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        return {}
    return response.json()

def parse_json(data):
    if data == {}:
        return {}
    return {
        "planned_consumption": int(data["MainArea"]["IBR_PlannedConsumption"].replace(' МВт*ч', '').replace(' ','')),
        "actual_consumption": int(data["MainArea"]["IBR_ActualConsumption"].replace(' МВт*ч', '').replace(' ','')),
        "planned_generation": int(data["MainArea"]["IBR_PlannedGeneration"].replace(' МВт*ч', '').replace(' ','')),
        "actual_generation": int(data["MainArea"]["IBR_ActualGeneration"].replace(' МВт*ч', '').replace(' ','')),
        "average_price": int(data["MainArea"]["IBR_AveragePrice"].replace(' руб./МВт*ч','').replace(' ',''))
            }

def iterate_through_dates(start, end):
    result = []
    current = start
    
    while current <= end:
        date_str = str(current)
        for hour in range(23):
            data = parse_json(download_data(date_str,str(hour)))
            if data == {}:
                continue
            data["date"] = str(datetime.combine(current,time(hour,0)))
            result.append(data)
            tm.sleep(1.)


        current += timedelta(days=1)
        tm.sleep(1.)

    return result

def main():
    filename = input("Файл сохранения (data.csv): ")
    start_unformatted = input("Дата начала (2022-01-01) ")
    end_unformatted = input("Дата конца (сегодняшний день) ")

    if filename == "":
        filename = "data.csv"

    if start_unformatted == "":
        start_unformatted = "2022-01-01"
    if end_unformatted == "":
        end_unformatted = str(date.today())

    start_split = list(map(int,start_unformatted.split("-")))
    end_split = list(map(int,end_unformatted.split("-")))

    start = date(start_split[0],start_split[1],start_split[2])
    end = date(end_split[0], end_split[1], end_split[2])

    df = pd.DataFrame(iterate_through_dates(start,end))
    df.to_csv(filename)

if __name__ == "__main__":
    main()


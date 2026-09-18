# Работаем с 
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from datetime import date, timedelta, datetime, time
import time as tm
import pandas as pd
import numpy as np
import requests

URL_TEMPLATE = "https://br.so-ups.ru/webapi/api/map/MapPartial?MapType=0&Date={date}&Hour={hour}&PowerSystemId=630000&SubjectId=75&ServiceMode=false"


def download_data(date,time):
    response_code = 429
    while response_code == 429:
        url = URL_TEMPLATE.format(date=date,hour=time)
        response = requests.get(url, verify=False)
        response_code = response.status_code
        if response_code != 200 and response_code != 429:
            return {"error_code": response_code}
        if response_code == 200:
            return response.json()
        print("Слишком много запросов! перепробуем...")
        tm.sleep(1)
    return {"error_code": 0}

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

    convenience_counter = 0
    counter_target = (end-start).days * 24
    
    while current <= end:
        convenience_counter += 1
        date_str = str(current)
        for hour in range(23):
            print("Запрашиваю {}/{}...",convenience_counter,counter_target)
            data = parse_json(download_data(date_str,str(hour)))
            if 'error_code' in data:
                print('Данные не получены с кодом: {}',data['error_code'])
                continue
            
            data["date"] = str(datetime.combine(current,time(hour,0)))
            result.append(data)
            print('Успех! данные добавлены')
            tm.sleep(0.5)


        current += timedelta(days=1)
        tm.sleep(0.5)

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


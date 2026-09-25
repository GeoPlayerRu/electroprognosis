# Работаем с 
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from datetime import date, timedelta, datetime, time
import time as tm
import pandas as pd
#import numpy as np
import requests

URL_TEMPLATE = "https://br.so-ups.ru/webapi/api/map/MapPartial?MapType=0&Date={date}&Hour={hour}&PowerSystemId=630000&SubjectId={subject}&ServiceMode=false"

def backup_on_fail(data: pd.DataFrame, path: str):
    new_path = path.replace('.csv','_backpup.csv')
    data.to_csv(new_path)


def download_data(date,time,subject):
    response_code = 429
    while response_code == 429:
        url = URL_TEMPLATE.format(date=date,hour=time,subject=subject)
        response = requests.get(url, verify=False)
        response_code = response.status_code
        if response_code != 200 and response_code != 429:
            return {"error_code": response_code}
        if response_code == 200:
            return response.json()
        print("Слишком много запросов! перепробуем...")
        tm.sleep(1)
    return {"error_code": 0}

def parse_json(data: dict):
    if not 'MainArea' in data or \
            not 'IBR_PlannedConsumption' in data['MainArea'] or \
            not 'IBR_ActualConsumption' in data['MainArea'] or \
            not 'IBR_PlannedGeneration' in data['MainArea'] or \
            not 'IBR_ActualGeneration' in data['MainArea'] or \
            not 'IBR_AveragePrice' in data['MainArea']:
                return data

    planned_consumption = data["MainArea"]["IBR_PlannedConsumption"].replace(' МВт*ч', '').replace(' ','')
    if planned_consumption == '-':
        planned_consumption = '0'
    actual_consumption = data["MainArea"]["IBR_ActualConsumption"].replace(' МВт*ч', '').replace(' ','')
    if actual_consumption == '-':
        actual_consumption = '0'
    planned_generation = data["MainArea"]["IBR_PlannedGeneration"].replace(' МВт*ч', '').replace(' ','')
    if planned_generation == '-':
        planned_generation = '0'
    actual_generation = data["MainArea"]["IBR_ActualGeneration"].replace(' МВт*ч', '').replace(' ','')
    if actual_generation == '-':
        actual_generation = '0'
    average_price = data["MainArea"]["IBR_AveragePrice"].replace(' руб./МВт*ч','').replace(' ','')
    if average_price == '-':
        average_price = '0'
    return {
            "planned_consumption" : int(planned_consumption),
            "actual_consumption" : int(actual_consumption),
            "planned_generation" : int(planned_generation),
            "actual_generation" : int(actual_generation),
            "average_price" : int(average_price),
            }

def iterate_through_dates(start, end, subject):
    result = []
    current = start

    convenience_counter = 0
    counter_target = (end-start).days * 24
    
    while current <= end:
        date_str = str(current)
        for hour in range(23):
            convenience_counter += 1
            print(f"Запрашиваю {convenience_counter}/{counter_target}...")
            downloaded = {}
            data = {'error_code' : 0}
            retries = 4
            while retries > 0:
                try:
                    downloaded = download_data(date_str,str(hour),subject)
                    data = parse_json(downloaded)
                    break
                except:
                    retries -= 1
                    if retries != 0:
                        print(f"Неизвестная ошибка! Попытка возобновить: {4-retries}/4")
                        tm.sleep(2)
                        continue
                    print('Загрузка данных была прервана на', str(datetime.combine(current,time(hour,0))))
                    print('Последние загруженные данные помещены в файл latest.json')
                    with open('latest.json', 'w') as file:
                        file.write(str(downloaded))
                    return result
            if 'error_code' in data:
                print('Данные не получены с кодом: {}.',data['error_code'])
                continue
            
            data["date"] = str(datetime.combine(current,time(hour,0)))
            result.append(data)
            print('Успех! данные добавлены')
            tm.sleep(0.1)


        current += timedelta(days=1)
        tm.sleep(0.1)

    return result

regions = {
        "75" : "Челябинская область",
        "33" : "Кировская область",
        "37" : "Курганская область",
        "53" : "Оренбургская область",
        "57" : "Пермский край",
        "80" : "Республика Башкортостан",
        "65" : "Свердловская область",
        "71" : "Тюменская область",
        "94" : "Удмуртская республика",
}

def main():
    subject = '-1'
    while not subject in regions.keys() and subject != '':
        subject = input(f"Доступные регионы:{'\n'.join([k+' - '+str(v) for k,v in regions.items()])}\nРегион (75):")
    filename = input("Файл сохранения (data.csv): ")
    start_unformatted = input("Дата начала (2022-01-01) ")
    end_unformatted = input("Дата конца (сегодняшний день) ")
    
    if subject == "":
        subject = "75"

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

    df = pd.DataFrame(iterate_through_dates(start,end,subject))
    df.to_csv(filename.replace('.csv',f'_{subject}.csv'))

if __name__ == "__main__":
    main()


#!/usr/bin/python

import pandas as pd
import numpy as np

RAW_PATH = 'data/raw/'
CLEAN_PATH = 'data/clean/'

HOURS_PER_DAY = 23
TARGET = 'actual_consumption'
PLAN = 'planned_consumption'

def load_and_clean(csv_path):
    """Читает CSV и возвращает почасовой DataFrame без пропусков.
 
    Дополнительный столбец ``actual_missing`` = True там, где исходное
    фактическое потребление равнялось нулю (значение восстановлено заполнением).
    """
    df = pd.read_csv(csv_path, parse_dates=['date'], index_col='date').sort_index()
    if df.index.duplicated().any():
        raise ValueError('В данных есть дубли по времени')
 
    missing = df[TARGET] == 0
    df = df.replace(0, np.nan).ffill().bfill()      # ffill - без утечки из будущего
    df['actual_missing'] = missing
    return df

path = input(f"Введите файл для предобработки. (./{RAW_PATH})")

raw_file_path = RAW_PATH + path
clean_file_path = CLEAN_PATH + path

# Обработка
load_and_clean(raw_file_path).to_csv(clean_file_path, index=True)

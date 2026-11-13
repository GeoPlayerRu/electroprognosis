#!/usr/bin/python

import pandas as pd
import numpy as np

RAW_PATH = 'data/raw/'
CLEAN_PATH = 'data/clean/'

path = input(f"Введите файл для предобработки. (./{RAW_PATH})")

raw_file_path = RAW_PATH + path
clean_file_path = CLEAN_PATH + path

# Обработка
df = pd.read_csv(raw_file_path, parse_dates=['date'], index_col='date').sort_index()

df = df.replace(0, np.nan).interpolate(limit_direction='both')

df.to_csv(clean_file_path, index=True)

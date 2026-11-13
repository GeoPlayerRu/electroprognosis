"""Общая предобработка данных (одинаковая для всех моделей проекта).

Правила:
* строки файла - почасовые значения, в сутках 23 часа (00-22);
* нули в столбцах - пропуски измерений. Заменяются на NaN и заполняются
  ПРОШЛЫМ значением (ffill), то есть без заглядывания в будущее;
* часы, где фактическое потребление было нулём, помечаются в маске
  и исключаются из расчёта метрик.
"""
import numpy as np
import pandas as pd

HOURS_PER_DAY = 23
TARGET = 'actual_consumption'
PLAN = 'planned_consumption'


def to_day_matrices(df):
    """Преобразует почасовой DataFrame в матрицы «день x час».

    Возвращает: days (DatetimeIndex), ACTUAL, PLAN, VALID.
    VALID[d, h] = False, если фактическое значение было пропущено.
    """
    grp = df.groupby(df.index.date)
    sizes = grp.size()
    bad = sizes[sizes != HOURS_PER_DAY]
    if len(bad):
        raise ValueError(f'Неполные сутки (не {HOURS_PER_DAY} часов): {list(bad.index[:5])}')

    days = pd.DatetimeIndex(sizes.index)
    actual = np.vstack(grp[TARGET].apply(lambda x: x.values).values)
    plan = np.vstack(grp[PLAN].apply(lambda x: x.values).values)
    valid = ~np.vstack(grp['actual_missing'].apply(lambda x: x.values).values)
    return days, actual, plan, valid

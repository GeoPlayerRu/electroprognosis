"""Единое разбиение данных (одинаковое для всех моделей проекта).

Протокол: скользящее окно (rolling origin) на один год.
Для каждого дня D прогнозного периода обучающая выборка = все сутки,
которые закончились ДО дня D (с начала данных до D-1 включительно).
Например, для 2 января обучение включает 1 января; для 1 января - всё до 31 декабря.
Данные дня D и позже в обучение не попадают.
"""
import numpy as np
import pandas as pd

FORECAST_START = '2025-01-01'
FORECAST_END = '2025-12-31'


def forecast_day_indices(days, start=FORECAST_START, end=FORECAST_END):
    """Индексы суток прогнозного периода внутри массива days."""
    mask = (days >= pd.Timestamp(start)) & (days <= pd.Timestamp(end))
    return np.where(mask)[0]


def rolling_origin(days, start=FORECAST_START, end=FORECAST_END, window_days=None):
    """Генератор (i, train_idx): i - индекс прогнозируемых суток,
    train_idx - индексы суток, доступных для обучения.

    window_days=None  - расширяющееся окно (всё с начала данных до D-1);
    window_days=N     - только последние N суток перед D (более короткий период).
    """
    for i in forecast_day_indices(days, start, end):
        lo = 0 if window_days is None else max(0, i - window_days)
        yield i, np.arange(lo, i)


def fixed_origin(days, start=FORECAST_START, end=FORECAST_END):
    """Одно обучение на всех сутках ДО начала прогнозного периода
    (старая постановка, для сравнения). Возвращает (train_idx, test_idx)."""
    test_idx = forecast_day_indices(days, start, end)
    train_idx = np.arange(0, test_idx[0])
    return train_idx, test_idx

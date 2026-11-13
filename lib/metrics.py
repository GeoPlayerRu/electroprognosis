"""Единые метрики (одинаковые для всех моделей проекта).

Два режима оценки:
* «все часы» - все 23 часа каждых суток;
* «пиковые часы» - PEAK_N самых нагруженных часов каждых суток, определённых
  ПО ФАКТУ. Пики используются только для оценки, при обучении не применяются.
Часы с пропущенным фактом (VALID == False) в метриках не участвуют.
"""
import numpy as np
import pandas as pd

PEAK_N = 3


def peak_mask(y_true, valid=None, n=PEAK_N):
    """Булева матрица: True для n самых нагруженных (по факту) часов каждых суток."""
    ranked = y_true.astype(float).copy()
    if valid is not None:
        ranked[~valid] = -np.inf          # восстановленный час пиком быть не может
    top = np.argsort(-ranked, axis=1)[:, :n]
    mask = np.zeros_like(y_true, dtype=bool)
    np.put_along_axis(mask, top, True, axis=1)
    return mask


def _scores(y, p):
    err = p - y
    return {'MAE': np.abs(err).mean(),
            'RMSE': np.sqrt((err ** 2).mean()),
            'MAPE, %': (np.abs(err) / y).mean() * 100}


def evaluate(y_true, y_pred, valid=None, n=PEAK_N):
    """Таблица метрик: все часы и пиковые часы."""
    if valid is None:
        valid = np.ones_like(y_true, dtype=bool)
    pk = peak_mask(y_true, valid, n) & valid
    rows = {'Все часы': _scores(y_true[valid], y_pred[valid]),
            f'Пиковые часы (топ-{n})': _scores(y_true[pk], y_pred[pk])}
    return pd.DataFrame(rows).T


def peak_hit_rate(y_true, y_pred, valid=None, n=PEAK_N):
    """Доля суток, где предсказанный максимум попал в число n фактических пиковых часов."""
    if valid is None:
        valid = np.ones_like(y_true, dtype=bool)
    pk = peak_mask(y_true, valid, n)
    pred_top = np.argmax(y_pred, axis=1)
    return pk[np.arange(len(pk)), pred_top].mean()

"""MLP-модель прогноза на сутки вперёд (23 часа сразу)."""
import numpy as np
import warnings
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.compose import TransformedTargetRegressor

import split

LAG_DAYS = 1

# Параметры и их обоснование - в ноутбуке (раздел «Параметры модели»).
MLP_PARAMS = dict(hidden_layer_sizes=(128, 64), activation='relu', solver='adam',
                  alpha=1e-3, learning_rate_init=1e-3, max_iter=1000,
                  early_stopping=True, validation_fraction=0.1, n_iter_no_change=30)


def calendar_features(d):
    dow, doy = d.dayofweek, d.dayofyear
    return [np.sin(2 * np.pi * dow / 7), np.cos(2 * np.pi * dow / 7),
            np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25),
            float(dow >= 5)]


def build_features(days, actual, plan, lag=LAG_DAYS, use_plan=True):
    """Матрица признаков X (по одной строке на сутки) и цели Y = actual.

    Строка суток i использует только данные суток < i (вчера и раньше),
    календарь суток i и, если use_plan, плановое потребление суток i
    (план публикуется заранее). Для первых `lag` суток признаков нет (NaN).
    """
    n = len(days)
    rows = []
    for i in range(n):
        if i < lag:
            rows.append(None)
            continue
        f = [actual[i - lag:i].ravel(), calendar_features(days[i])]
        if use_plan:
            f.append(plan[i])
        rows.append(np.concatenate(f))
    width = len(next(r for r in rows if r is not None))
    X = np.array([r if r is not None else np.full(width, np.nan) for r in rows])
    return X, actual


def make_mlp(seed):
    return TransformedTargetRegressor(
        regressor=make_pipeline(StandardScaler(), MLPRegressor(random_state=seed, **MLP_PARAMS)),
        transformer=StandardScaler())


def _fit_predict(X, Y, train_idx, test_idx, n_seeds):
    """Обучает n_seeds сетей на train_idx и усредняет их прогноз для test_idx."""
    train_idx = train_idx[~np.isnan(X[train_idx]).any(axis=1)]    # дни без лага выбрасываем
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        preds = [make_mlp(s).fit(X[train_idx], Y[train_idx]).predict(X[test_idx])
                 for s in range(n_seeds)]
    return np.mean(preds, axis=0)


def rolling_forecast(days, X, Y, start=split.FORECAST_START, end=split.FORECAST_END,
                     window_days=None, n_seeds=3, n_jobs=1, verbose=True):
    """Скользящее окно: для каждых суток прогнозного периода модель обучается заново
    на всех суток до предыдущего дня включительно."""
    from joblib import Parallel, delayed
    jobs = list(split.rolling_origin(days, start, end, window_days))
    if verbose:
        print(f'Скользящее окно: {len(jobs)} суток x {n_seeds} сетей', flush=True)
    results = Parallel(n_jobs=n_jobs, verbose=5 if verbose else 0)(
        delayed(_fit_predict)(X, Y, tr, np.array([i]), n_seeds) for i, tr in jobs)
    test_idx = np.array([i for i, _ in jobs])
    return test_idx, np.vstack(results)


def fixed_forecast(days, X, Y, start=split.FORECAST_START, end=split.FORECAST_END, n_seeds=3):
    """Старая постановка: одно обучение на данных до начала прогнозного периода."""
    train_idx, test_idx = split.fixed_origin(days, start, end)
    return test_idx, _fit_predict(X, Y, train_idx, test_idx, n_seeds)


def cached_rolling(name, days, X, Y, start=split.FORECAST_START, end=split.FORECAST_END,
                   window_days=None, n_seeds=3, n_jobs=1, cache_dir='results', recompute=False):
    """rolling_forecast с кэшем на диске: повторный запуск ноутбука не пересчитывает модель."""
    import os
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f'rolling_{name}_w{window_days}_s{n_seeds}_{start}_{end}.npz')
    if os.path.exists(path) and not recompute:
        z = np.load(path)
        print('Загружено из кэша:', path)
        return z['test_idx'], z['pred']
    test_idx, pred = rolling_forecast(days, X, Y, start, end, window_days, n_seeds, n_jobs)
    np.savez(path, test_idx=test_idx, pred=pred)
    return test_idx, pred

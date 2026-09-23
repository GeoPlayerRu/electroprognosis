import pandas as pd

dataframes_paths = [
    "data.csv",
    "data_part2.csv",
    "data_part3.csv",
    "data_part4.csv",
    "data_partial.csv",
]

dfs = [
    pd.read_csv(
        path,
        parse_dates=["date"],
        index_col="date"
    ).drop(columns=["Unnamed: 0"], errors="ignore")
    for path in dataframes_paths
]

concated = pd.concat(dfs, axis=0)

concated = concated[
    ~concated.index.duplicated(keep="last")
]

concated = concated.sort_index()

concated.to_csv("combined.csv")

print(concated.head())

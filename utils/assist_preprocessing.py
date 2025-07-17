import pandas as pd
from sklearn.preprocessing import StandardScaler

def drop_nulls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=df.columns)
    if df.empty:
        raise ValueError("All rows removed after dropping nulls.")
    return df

def normalize_covariates(df: pd.DataFrame, treatment: str, outcome: str) -> pd.DataFrame:
    reserved_cols = [col for col in [treatment, outcome] if col in df.columns]
    num_cols = [col for col in df.select_dtypes(include="number").columns if col not in reserved_cols]
    cat_cols = [col for col in df.select_dtypes(exclude="number").columns if col not in reserved_cols]

    if num_cols:
        scaler = StandardScaler()
        df_num = pd.DataFrame(
            scaler.fit_transform(df[num_cols]),
            columns=num_cols,
            index=df.index
        )
    else:
        df_num = pd.DataFrame(index=df.index)

    df_out = pd.concat([df[reserved_cols + cat_cols], df_num], axis=1)
    return df_out
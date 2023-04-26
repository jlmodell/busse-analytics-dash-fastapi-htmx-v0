import pandas as pd


def pipeline_to_dataframe(func, pipeline):
    return pd.DataFrame(list(func(pipeline)))


def excel_to_dataframe(path):
    return pd.read_excel(path)


def process_dataframe(df):
    if "postal" in df.columns:
        df["postal"] = df["postal"].astype(str)
        df["postal"] = df["postal"].str.zfill(5)

    if "name" in df.columns:
        df["name"] = df["name"].str.upper()

    if "addr" in df.columns:
        df["addr"] = df["addr"].str.upper()

    if "city" in df.columns:
        df["city"] = df["city"].str.upper()

    if "state" in df.columns:
        df["state"] = df["state"].str.upper()

    cols_to_keep = [
        "invoice_date",
        "period",
        "name",
        "addr",
        "city",
        "state",
        "postal",
        "part",
        "cost",
        "rebate",
        "ship_qty_as_cs",
        "gpo",
        "contract",
    ]

    return df[cols_to_keep]


def group_by(df):
    return (
        df[["part", "contract", "cost", "rebate", "ship_qty_as_cs"]]
        .groupby(["part", "contract"])
        .sum()
    )

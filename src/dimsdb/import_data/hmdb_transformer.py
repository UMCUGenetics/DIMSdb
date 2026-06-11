from pandas import DataFrame

def transform_hmdb_df(hmdb_df: DataFrame) -> DataFrame:
    hmdb_df.rename(
        columns={
            "HMDB_key": "hmdb_key",
            "HMDB_ID": "hmdb_id",
            "sec_HMDB_ID": "sec_hmdb_id",
            "HMDB_name": "name",
            "Chemical_formula": "chem_formula",
            "MNeutral": "theor_mz",
            "descr": "description",
        },
        inplace=True,
    )

    return hmdb_df

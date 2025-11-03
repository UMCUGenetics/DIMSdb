import pandas as pd
import rdata

from src.dimsdb.database import engine

def read_hmdb_file(file):
    parsed = rdata.parser.parse_file(file)
    hmdb_df = rdata.conversion.convert(parsed, default_encoding="utf8")
    hmdb_df = pd.DataFrame(hmdb_df.get("HMDB_V5_DIMSpect"))
    hmdb_df.rename(columns={'HMDB_key': 'hmdb_key', 'HMDB_ID': 'hmdb_id',
                            'sec_HMDB_ID': 'sec_hmdb_id', 'HMDB_name': 'name',
                            'Chemical_formula': 'chem_formula', 'MNeutral': 'theor_mz'}, inplace=True)
    hmdb_df['description'] = ""
    return hmdb_df


def add_hmdb_table(hmdb_df):
    with engine.begin() as conn:
        hmdb_df.to_sql(name='hmdb', con=conn, if_exists='append', index=False, chunksize = 10000)


def main():
    path_file = "/Users/aluesin2/Documents/DIMSdb/HMDB_data/DIMSpect_HMDB_V5.RData"
    hmdb_df = read_hmdb_file(path_file)
    add_hmdb_table(hmdb_df)


if __name__ == "__main__":
    main()


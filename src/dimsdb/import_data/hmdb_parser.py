import pandas as pd
from pandas import DataFrame
from pathlib import Path
import rdata

def parse_hmdb_rdata_file(file_path: Path) -> DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Bestand bestaat niet: {file_path}")

    parsed_hmdb_file = rdata.parser.parse_file(file_path)
    hmdb_df = rdata.conversion.convert(parsed_hmdb_file, default_encoding="utf8")
    hmdb_df = pd.DataFrame(hmdb_df.get("dimspect_df"))
    return hmdb_df

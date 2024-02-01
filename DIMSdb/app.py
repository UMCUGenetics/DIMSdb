from database import engine, SQLModel
from read_rdata_testdata import parse_rdata
# from .models import *

def main():
    # SQLModel.metadata.drop_all(engine)
    # SQLModel.metadata.create_all(engine)

    path_name = "/Users/aluesin2/Documents/DIMSdb/test_data/"
    run_names = ["RES_PL_20231002_plasma"]
    for run_name in run_names:
        print(run_name)
        # file_neg = path_name + run_name + '/outlist_ident_space_negative.RData'
        file_neg = path_name + run_name + '/outlist_identified_negative.RData'
        print(file_neg)
        parse_rdata(file_neg, run_name)
        # file_pos = path_name + run_name + '/outlist_ident_space_positive.RData'
        file_pos = path_name + run_name + '/outlist_identified_positive.RData'
        print(file_pos)
        parse_rdata(file_pos, run_name)

if __name__ == "__main__":
    main()
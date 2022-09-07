"""
Take the file from:
    https://ui.adsabs.harvard.edu/abs/2021ApJ...923..129J/abstract

and crossmatched with TIC8 to get magnitudes for all cluster members

Output the new crossmatched table as csv file
"""
from contextlib import contextmanager
import pymysql
import pandas as pd
import numpy as np

def query_object(gaia_id):
    """
    Get magnitudes for given object
    """
    qry = """
        SELECT
        GAIAmag,e_GAIAmag,Bmag,e_Bmag,
        Vmag,e_Vmag,umag,e_umag,
        gmag,e_gmag,rmag,e_rmag,imag,
        e_imag,zmag,e_zmag,Jmag,e_Jmag,
        Hmag,e_Hmag,Kmag,e_Kmag
        FROM tic8
        WHERE gaia_id={}
        """.format(gaia_id)
    print(qry)

    with open_db() as cur:
        cur.execute(qry)
        res = cur.fetchone()
    return res

@contextmanager
def open_db(host='ngtsdb', db='catalogues'):
    """
    Connect to database
    """
    with pymysql.connect(host=host, db=db) as conn:
        with conn.cursor() as cur:
            yield cur



if __name__ == "__main__":
    # load up the list of cluster members from the
    # Jaehnig K., Bird J., Holley-Bockelmann K. 2021 paper
    members_path = "open_cluster_membership_apjac1d51t2_mrt.txt"

    # load the catalog file
    catalog = pd.read_fwf(members_path,
                          colspecs=[(0, 17),
                                    (17, 37),
                                    (37, 62),
                                    (62, 83),
                                    (83, 108),
                                    (108, 129),
                                    (129, 153),
                                    (153, 174),
                                    (174, 198),
                                    (198, 219),
                                    (219, 243),
                                    (243, 264),
                                    (264, 275),
                                    (275, 290),
                                    (290, 294)],
                          skiprows=30, header=0)

    table = []
    for s in catalog['source_ID'][:10]:
        results = query_object(s)
        table.append(results)
    table = np.array(table)

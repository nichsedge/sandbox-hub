import pandas as pd
import numpy as np
import ast
from sqlalchemy import create_engine

db_params = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",  # Change to your database host
    "port": "5432",  # Change to your database port
}
db_url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
engine = create_engine(db_url)

import requests

dpr = "https://caleg.zakiego.com/api/dpr-ri/dapil/3201"
dpd = "https://caleg.zakiego.com/api/dpd/dapil/32"
dprd_provinsi = "https://caleg.zakiego.com/api/dprd-provinsi/dapil/320001"
dprd_kabupaten = "https://caleg.zakiego.com/api/dprd-kabupaten-kota/dapil/327701"


def req(url, tbl_name):
    endpoint = url
    data = requests.get(endpoint).json()
    df = pd.DataFrame(data["data"])

    for col in df.columns:
        df[col] = df[col].astype(str)

    df.to_sql(
        name=tbl_name,
        con=engine,
        schema="personal",
        if_exists="replace",
        method="multi",
        index=False,
    )


req(url=dprd_kabupaten, tbl_name="dprd_kabupaten")

# for col in ['riwayatPekerjaan', 'statusHukum', 'riwayatPendidikan',
#        'riwayatKursusDiklat', 'riwayatOrganisasi', 'riwayatPenghargaan',
#        'programUsulan', 'motivasi']:
#     df[col] = df[col].to_json(orient='records')

# # Denormalize columns containing dictionaries
# for col in df.columns:
#     try:
#         df[col].fillna('[]', inplace=True)
#         df[col] = df[col].apply(ast.literal_eval)

#         # if isinstance(df[col][0], list):
#         df = pd.concat([df.drop(col, axis=1), pd.json_normalize(df[col].explode())], axis=1)
#     except:
#         print(col)

# def explode_columns_with_arrays(df):
#     for col in df.columns:
#         if df[col].apply(lambda x: isinstance(x, list)).all():
#             df = df.explode(col)
#     return df

# # Explode columns containing arrays
# df = explode_columns_with_arrays(df)

# # Function to convert dictionary columns to JSON strings
# def convert_dict_columns_to_json(df):
#     for col in df.columns:
#         if df[col].apply(lambda x: isinstance(x, dict)).all():
#             df[col] = df[col].apply(json.dumps)
#     return df

# # Convert dictionary columns to JSON strings
# df = convert_dict_columns_to_json(df)

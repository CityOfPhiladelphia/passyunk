'''
Oracle helper functions - not all functions may be used by a parent script
'''
import cx_Oracle
import sys
import petl as etl
import numpy as np
import pandas as pd

def format_data(df, conn, table): 
    '''
    Takes a pandas dataframe and 
    1. Ensures column order exactly matches the database's, and are UPPERCASE
    2. Drops any columns not in the database table
    3. Returns the data as a list of tuples
    '''
    with conn.cursor() as cur:
        statement = f"SELECT * FROM {table} WHERE ROWNUM = 1"
        cur.execute(statement)
        desc = cur.description
        
    df.columns = [col.upper() for col in df.columns]

    oracle_order = []
    for oracle_col in desc: 
        if oracle_col[0] not in df.columns:
            raise(IndexError(f'Column "{oracle_col[0]}" from database table "{table}" not in dataframe'))
        oracle_order.append(oracle_col[0])
    
    df = df.reindex(columns=[col for col in oracle_order]) # Drops columns not in db table
    df = df.replace({
        '': None, 
        np.nan: None}).astype('object') # As type 'object' is needed for Nones
    data = list(df.to_records(index=False))
    
    return data

def connect_to_db(db_creds): 
    '''
    Return an Oracle Connection using a dictionary of credentials
    '''
    dsn = cx_Oracle.makedsn(
        host=db_creds['dsn']['host'], 
        port=db_creds['dsn']['port'], 
        service_name=db_creds['dsn']['service_name'])
    conn = cx_Oracle.connect(
        user=db_creds['username'], 
        password=db_creds['password'], 
        dsn=dsn)
    return conn

def append_data(all_data, conn, table): 
    '''
    Prepares the APPEND query, and runs it
    '''
    print(f'Appending to "{table}"')
    start_pos = 0
    batch_size = 15000
    l = [x + 1 for x in list(range(len(all_data[0])))] # Length of the first record
    values = ', :'.join(map(str, l))
    execution_statement = f"INSERT INTO {table} VALUES (:{values})"
    while True:
        print(f'    appending rows [{start_pos}:{start_pos + batch_size-1}]')
        data = all_data[start_pos:start_pos + batch_size]
        if data == []: 
            break
        start_pos += batch_size
        with conn.cursor() as cur:
            try: 
                cur.executemany(execution_statement, data)
                print(f"Successfully appended {cur.rowcount} rows to table '{table}'")
            except Exception as e: 
                print('Execution Statement Failed:')
                print(f'{execution_statement}')
                print('data[0:5]:')
                for row in data[0:5]: 
                    print(f'    {row}')
                print('data[-5:]:')
                for row in data[-5:]: 
                    print(f'    {row}')
                print(e)
                sys.exit()

def append_df(df, conn, table): 
    all_data = format_data(df, conn, table) # Returns as list/records
    append_data(all_data, conn, table)

def append_petl(all_data, conn, table): 
    data_list = list(etl.records(all_data))
    append_data(data_list, conn, table)
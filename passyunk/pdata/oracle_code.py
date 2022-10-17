'''
Oracle helper functions - not all functions may be used by a parent script.

Note that all DDL statements auto-commit even if the transaction is rolled back. 
This includes ALTER, CREATE, DROP, RENAME, TRUNCATE, etc., so avoid those statements!
See https://docs.oracle.com/cd/B14117_01/server.101/b10759/statements_1001.htm#i2099120
'''
import cx_Oracle
import sys
import petl as etl
import numpy as np
import pandas as pd
import time

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

def commit_transactions(db_conn, commit: bool): 
    if commit: 
        db_conn.rollback()
    else: 
        db_conn.commit()
    print(f'All database transactions were {"COMMITTED" if commit else "ROLLED BACK"}')

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

def append_data(all_data, conn, table, truncate: bool): 
    '''
    Prepares the APPEND query, and runs it
    '''
    print(f'Appending to "{table}"')
    start_pos = 0
    batch_size = 15000
    l = [x + 1 for x in list(range(len(all_data[0])))] # Length of the first record
    values = ', :'.join(map(str, l))
    if truncate: 
        execution_statement = f"DELETE FROM {table}" 
        with conn.cursor() as cur:
            cur.execute(execution_statement)
        print(f'Successfully deleted {cur.rowcount} rows from table "{table}"')
    execution_statement = f"INSERT INTO {table} VALUES (:{values})"
    while True:
        data = all_data[start_pos:start_pos + batch_size]
        if data == []: 
            break
        print(f'    appending rows [{start_pos}:{start_pos + batch_size-1}]')
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

def append_df(df, conn, table, truncate): 
    all_data = format_data(df, conn, table) # Returns as list/records
    append_data(all_data, conn, table, truncate)

def append_petl(all_data, conn, table, truncate): 
    print('Starting timer')
    start = time.time()
    # etl.todataframe() is 2x faster than list(etl.records()) and 6x faster than looping with etl.rowslice(), which got worse with time
    df = etl.todataframe(all_data)
    print(f'    time: {time.time() - start:,.1f} seconds')
    append_df(df, conn, table, truncate)
    print(f'Finished in {time.time() - start:,.1f} seconds')
    
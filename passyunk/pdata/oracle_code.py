'''
Oracle helper functions - not all functions may be used by a parent script
'''
import cx_Oracle
import numpy as np
import pandas as pd

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

def check_db_latest(db_conn, table, columns): 
    '''
    Checks for latest values in a table from several columns
    '''
    execution_statement = f'SELECT MAX (GREATEST ({columns})) FROM {table}'
    with db_conn.cursor() as cur: 
        try: 
            cur.execute(execution_statement)
            return cur.fetchone()
        except Exception as e: 
            print('Execution Statement Failed:')
            print(f'{execution_statement}')
            raise e

def db_to_df(db_conn, table): 
    '''
    Returns the data from a SELECT statement as a pandas dataframe
    '''
    with db_conn.cursor() as cur: 
        # Get existing data from database
        execution_statement = f'SELECT * FROM {table}'
        cur.execute(execution_statement)
        rv = cur.fetchall()
        rv_df = (pd.DataFrame
            .from_records(rv, columns=[desc[0] for desc in cur.description]))
    return rv_df

def append_data(df, conn, table): 
    '''
    Calls format_data, then prepares the APPEND query, and runs it
    Allows Oracle to accept dates in 'YYYY-MM-DD' format
    '''
    data = format_data(df, conn, table) # Returns as list/records

    if len(data) > 0: 
        l = [x + 1 for x in list(range(len(data[0])))] # Length of the first record
        values = ', :'.join(map(str, l))
        execution_statement = f"INSERT INTO {table} VALUES (:{values})"
        
        with conn.cursor() as cur:
            cur.execute('ALTER SESSION SET NLS_DATE_FORMAT="YYYY-MM-DD"')
            try: 
                cur.executemany(execution_statement, data)
                print(f"Successfully appended {cur.rowcount} rows to table '{table}'")
            except Exception as Error: 
                print('Execution Statement Failed:')
                print(f'{execution_statement}')
                print('data[0:5]:')
                for row in data[0:5]: 
                    print(f'    {row}')
                print('data[-5:]:')
                for row in data[-5:]: 
                    print(f'    {row}')
                raise Error
    else: 
        print('Not appending - lenth of data is 0')

def delete_data(np_array, db_conn, table, column): 
    '''
    Runs a delete query where one column contains a delete key
    '''
    if len(np_array) != 0: 
        execution_statement = f"DELETE FROM {table} WHERE {column} = :1"
        data = list(zip(np_array))
        with db_conn.cursor() as cur:
            try: 
                cur.executemany(execution_statement, data)
                print(f"Successfully deleted {cur.rowcount} rows from table '{table}'")
            except Exception as e: 
                print('Execution Statement Failed:')
                print(f'{execution_statement}')
                raise e
    else: 
        print('Not deleting - Array has length 0')

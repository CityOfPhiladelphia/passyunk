'''
Oracle helper functions - not all functions may be used by a parent script
'''
import cx_Oracle

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

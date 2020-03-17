import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect(key="1jsruJoeQ4LSbh8RlRGmiyDNGsoWZewqDKPd12M9jj20"):
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('gsheets_infos.json', scope)
    client = gspread.authorize(creds)

    # Open the workbook
    workbook = client.open_by_key(key)
    
    return workbook

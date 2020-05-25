import os
import json

from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect(key="1jsruJoeQ4LSbh8RlRGmiyDNGsoWZewqDKPd12M9jj20"):
    # use creds to create a client to interact with the Google Drive API
    load_dotenv()
    GSHEETS_CREDENTIALS = os.getenv("GSHEETS_CREDENTIALS")
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GSHEETS_CREDENTIALS), scope)
    client = gspread.authorize(creds)

    # Open the workbook
    workbook = client.open_by_key(key)

    return workbook
    
    
def update(sheet, Modifs):
    """Met à jour la feuille sheet avec les modifications indiquées dans Modifs.
    Modifs doit être une liste de tuples (ligne, colonne, valeur)."""
    
    lm = max([l for (l, c, v) in Modifs])       # ligne max de la zone à modifier
    cm = max([c for (l, c, v) in Modifs])       # colonne max de la zone à modifier

    # Récupère toutes les valeurs sous forme de cellules gspread
    cells = sheet.range(1, 1, lm+1, cm+1)   # gspread indexe à partir de 1 (comme les gsheets)

    cells_to_update = []
    for (l, c, v) in Modifs:
        cell = [cell for cell in cells if cell.col == c+1 and cell.row == l+1][0]    # on récup l'objet Cell correspondant aux coords à modifier
        cell.value = "" if v is None else v     # cells : ([<L1C1>, <L1C2>, ..., <L1Ccm>, <L2C1>, <L2C2>, ..., <LlmCcm>]
        cells_to_update.append(cell)

    sheet.update_cells(cells_to_update)

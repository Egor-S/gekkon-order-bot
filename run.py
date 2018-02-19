import httplib2
from apiclient import discovery
from oauth2client import service_account

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "google_service.json"

credentials = service_account.ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
http = credentials.authorize(httplib2.Http())
discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

spread_id = "1s8wkQgta6EqCC9UF8zDrom6YRzN3KYzDLugg4uL-vqA"
result = service.spreadsheets().values().get(spreadsheetId=spread_id, range="list0!A1:C4").execute()
print(result)

# IT'S WORKING!!!

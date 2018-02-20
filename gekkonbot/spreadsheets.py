import httplib2
import apiclient
from oauth2client import service_account


DISCOVERY_URL = "https://sheets.googleapis.com/$discovery/rest?version=v4"


class ItemsCatalog:
    """
    Provides list of available items for requesting
    """
    service = None
    spreadsheet_id = None
    range = "items!A3:C100"  # default table range

    def __init__(self, credentials, table_id):
        """
        :param credentials: ServiceAccountCredentials
        :param table_id: Id of Google Spreadsheet
        """
        http = credentials.authorize(httplib2.Http())
        self.service = apiclient.discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URL)
        self.spreadsheet_id = table_id

    def all(self):
        """
        :return: List of items (code, name, description)
        """
        query = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=self.range)
        response = query.execute()
        rows = response.get('values', [])
        catalog = []
        for row in rows:
            try:
                code = int(row[0])
                catalog.append((code, *row[1:]))
            except ValueError:
                continue
        return catalog

    def get_category(self, category):
        """
        :param category: Category number
        :return: Items from category
        """
        catalog = self.all()
        subcatalog = []
        for item in catalog:
            if item[0] // 100 == category:
                subcatalog.append(item)
        return subcatalog


def get_credentials(credentials_path):
    """
    :param credentials_path: Path to credentials json file
    :return: ServiceAccountCredentials
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    return service_account.ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scopes=scopes)

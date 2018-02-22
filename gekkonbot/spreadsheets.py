import httplib2
import apiclient
import datetime as dt
from oauth2client import service_account


DISCOVERY_URL = "https://sheets.googleapis.com/$discovery/rest?version=v4"
UPDATE_DELAY = 1000 * 60 * 30  # 30 minutes


class SpreadsheetService:
    """
    Provides service to work with Google Spreadsheets
    """
    def __init__(self, credentials):
        self._http = credentials.authorize(httplib2.Http())
        self.service = apiclient.discovery.build('sheets', 'v4', http=self._http, discoveryServiceUrl=DISCOVERY_URL)


class ItemsCatalog(SpreadsheetService):
    """
    Provides list of available items for requesting
    """
    range = "items!A3:C"  # default catalog range

    def __init__(self, credentials, table_id):
        """
        :param credentials: ServiceAccountCredentials
        :param table_id: Id of Google Spreadsheet
        """
        super(ItemsCatalog, self).__init__(credentials)
        self.spreadsheet_id = table_id
        self._cache = {}
        self.last_update = 0  # timestamp
        self.all()  # to preload catalog

    def all(self):
        """
        :return: Dict of items {code: (name, description)}
        """
        now = dt.datetime.now().timestamp()
        if now - self.last_update > UPDATE_DELAY:
            query = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=self.range)
            response = query.execute()
            rows = response.get('values', [])
            self._cache = {}
            for row in rows:
                try:
                    code = int(row[0])
                    self._cache[code] = row[1:]
                except ValueError:
                    continue
            self.last_update = now
        return self._cache

    def get_category(self, category):
        """
        :param category: Category number
        :return: Items list from category
        """
        catalog = self.all()
        subcatalog = [(code, *catalog[code]) for code in catalog if code // 100 == category]
        return subcatalog

    def get(self, code):
        """
        :param code: Item code
        :return: Item
        """
        catalog = self.all()
        item = (code, *catalog[code])
        return item


class OrderList(SpreadsheetService):
    """
    Provides storage for orders
    """
    range = "orders!A:F"  # default append range
    id_range = "orders!A2:A"  # default id range

    def __init__(self, credentials, table_id):
        """
        :param credentials: ServiceAccountCredentials
        :param table_id: Id of Google Spreadsheet
        """
        super(OrderList, self).__init__(credentials)
        self.spreadsheet_id = table_id
        self.last_id = 0
        self.get_last_id()

    def get_last_id(self):
        """
        Find max id in first column
        """
        query = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=self.id_range)
        response = query.execute()
        column = list(zip(*response.get('values', [['0']])))[0]
        self.last_id = max(map(int, column))

    def new(self, item, count, customer):
        """
        :param item: Item code
        :param count: Items count
        :param customer: Customer name
        :return:
        """
        time = dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.last_id += 1
        order_id = "{:05}".format(self.last_id)
        body = {
            'values': [[order_id, str(item[0]), item[1], str(count), customer, time]]
        }
        query = self.service.spreadsheets().values().append(spreadsheetId=self.spreadsheet_id, range=self.range,
                                                            body=body, valueInputOption="RAW")
        result = query.execute()
        return order_id


def get_credentials(credentials_path):
    """
    :param credentials_path: Path to credentials json file
    :return: ServiceAccountCredentials
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    return service_account.ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scopes=scopes)

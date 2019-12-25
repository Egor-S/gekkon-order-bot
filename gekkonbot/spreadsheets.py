import httplib2
import apiclient
import re
import datetime as dt
import hashlib
from oauth2client import service_account


DISCOVERY_URL = "https://sheets.googleapis.com/$discovery/rest?version=v4"
UPDATE_DELAY = 1000 * 60 * 30  # 30 minutes
RECENT_SIZE = 6
MSK_TZ = dt.timezone(dt.timedelta(hours=3))


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

    def __init__(self, credentials, table_config):
        """
        :param credentials: ServiceAccountCredentials
        :param table_id: Id of Google Spreadsheet
        """
        super(ItemsCatalog, self).__init__(credentials)
        self.spreadsheet_id = table_config['table']
        self.range = table_config['sheet'] + "!" + table_config['range']
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
            self._cache = []
            category_name = "Unnamed category"
            category_items = {}

            for i, row in enumerate(rows):
                if len(row) > 0:
                    if row[0]:  # category header
                        if len(category_items) > 0:
                            self._cache.append({
                                'title': category_name,
                                'items': category_items
                            })
                        category_name = row[0].split(":")[-1].strip()
                        category_items = {}
                    elif len(row) < 3:
                        print("No name in row #{}".format(i + 2))
                        continue
                    else:
                        if not row[2]:  # skip subitem
                            continue
                        try:
                            code = int(row[1])
                            name_search = re.search('"([^"]+)"', row[2])
                            if name_search:
                                category_items[code] = (name_search.group(1), row[2])
                            else:
                                category_items[code] = (row[2], row[2])
                        except ValueError:  # no code
                            print("No code in row #{}".format(i + 2))
                            continue

            if len(category_items) > 0:
                self._cache.append({
                    'title': category_name,
                    'items': category_items
                })
            self.last_update = now
        return self._cache

    def get_category(self, category):
        """
        :param category: Category number
        :return: Items list from category
        """
        catalog = self.all()
        subcatalog = [(code,) + tuple(catalog[category]['items'][code]) for code in catalog[category]['items']]
        return subcatalog

    def get(self, category, code):
        """
        :param category: Item category id
        :param code: Item code
        :return: Item
        """
        catalog = self.all()
        item = (code,) + tuple(catalog[category]['items'][code])
        return item

    def get_categories(self):
        """
        :return: List of categories
        """
        categories = []
        for i, category in enumerate(self._cache):
            categories.append((i, category['title']))
        return categories


class OrderList(SpreadsheetService):
    """
    Provides storage for orders
    """

    def __init__(self, credentials, table_config):
        """
        :param credentials: ServiceAccountCredentials
        :param table_id: Id of Google Spreadsheet
        """
        super(OrderList, self).__init__(credentials)
        self.spreadsheet_id = table_config['table']
        self.range = table_config['sheet'] + "!" + table_config['range']
        self.id_range = table_config['sheet'] + "!" + table_config['id-range']
        self.last_id = 0
        self.get_last_id()

    def get_last_id(self):
        """
        Find max id in first column
        """
        query = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=self.id_range)
        response = query.execute()
        column = [x[0] for x in response.get('values', [['0']]) if len(x)]
        self.last_id = max(map(int, column))

    def new(self, item, count, customer, deadline, destination, comment):
        """
        :param item: Item code
        :param count: Items count
        :param customer: Customer name
        :param deadline: Deadline date
        :param destination: Destination school
        :param comment: Purpose for order
        :return:
        """
        time = dt.datetime.now(tz=MSK_TZ).strftime("%d.%m.%Y %H:%M:%S")
        self.last_id += 1
        order_id = "{:05}".format(self.last_id)
        body = {
            'values': [[order_id, item[0], item[1], count, customer, time, '', '', '', '', deadline, destination, comment]]
        }
        query = self.service.spreadsheets().values().append(spreadsheetId=self.spreadsheet_id, range=self.range,
                                                            body=body, valueInputOption="RAW")
        result = query.execute()
        return order_id


class DestinationList(SpreadsheetService):
    """
    Provides list of available destinations
    """

    def __init__(self, credentials, table_config):
        super(DestinationList, self).__init__(credentials)
        self.spreadsheet_id = table_config['table']
        self.range = table_config['sheet'] + "!" + table_config['range']
        self._cache = []
        self.recent = []
        self.last_update = 0  # timestamp
        self.all()  # to preload destinations

    def all(self):
        now = dt.datetime.now().timestamp()
        if now - self.last_update > UPDATE_DELAY:
            query = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=self.range)
            response = query.execute()
            rows = response.get('values', [])
            self._cache = []
            for row in rows:
                if not len(row):
                    continue
                md5 = hashlib.new('md5')
                md5.update(row[0].encode('utf-8'))
                self._cache.append((row[0], md5.hexdigest()))
            self.last_update = now
        return self._cache

    def get_recent(self):
        return self.recent

    def update_recent(self, dst_hash):
        for i in range(len(self.recent)):
            if self.recent[i][1] == dst_hash:
                self.recent.pop(i)
                break
        self.recent.insert(0, (self.get(dst_hash), dst_hash))
        if len(self.recent) > RECENT_SIZE:
            self.recent = self.recent[:RECENT_SIZE]

    def get(self, query_hash):
        for dst, dst_hash in self._cache:
            if dst_hash == query_hash:
                return dst
        raise IndexError

    def search(self, query):
        destinations = self.all()
        query = query.lower()
        results = []
        for dst, dst_hash in destinations:
            if query in ' {} '.format(dst.lower()):
                results.append((dst, dst_hash))
        return results


def get_credentials(credentials_path):
    """
    :param credentials_path: Path to credentials json file
    :return: ServiceAccountCredentials
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    return service_account.ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scopes=scopes)

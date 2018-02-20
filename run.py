from gekkonbot.spreadsheets import get_credentials, ItemsCatalog

credentials = get_credentials("google_service.json")
catalog = ItemsCatalog(credentials, "1s8wkQgta6EqCC9UF8zDrom6YRzN3KYzDLugg4uL-vqA")
print(catalog.all())
print("*****")
print(catalog.get_category(2))

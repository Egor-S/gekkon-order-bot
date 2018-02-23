## Описание
> Sorry, what?

## Зависимости
Необходимая версия интерпретатора `Python 3`.
Для установки зависимостей используйте соответствующий `pip` (глоабыльный или из `virtualenv`):

```bash
pip install -r requirements.txt
```

## Credentials
Поместите в корень проекта:

- `google_service.json` данные Service Google Account (из Google API Console)
- `telegram.secret` с Telegram Bot Token внутри (от @BotFather)

## Другие настройки
Предоставьте доступ к Google таблицам пользователю из файла `google_service.json`.
`chat_id` можно узнать у бота с помощью команды `/chatid`.

Замените на корректные Google Spreadsheet Ids и `chat_id` в `run.py`.
При необходимости замените значение диапазона `range` в классе `ItemsCatalog` в файле `spreadsheets.py`.

## Использование
```bash
cd ~/gekkon-order-bot
```

Для глобального инерпретатора Python
```bash
python run.py
```

Для `virtualenv`
```bash
venv/bin/python run.py
```

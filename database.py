from peewee import SqliteDatabase, Model, IntegerField, TextField, DateField, TimeField
from datetime import datetime as dt


db = SqliteDatabase("database.db")


class Search(Model):
    """
    Model class to store the scraped data
    """

    __instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Search, cls).__new__(cls)
        return cls.__instance

    id = IntegerField(primary_key=True)
    id.auto_increment = True

    website = TextField()
    key_word = TextField()
    date = DateField(default=dt.now().date())
    time = TimeField(default=str(dt.now().time())[:5])
    class Meta:
        database = db


if not db.table_exists("Data"):
    db.create_tables([Search])

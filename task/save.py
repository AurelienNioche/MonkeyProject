from sqlite3 import connect, OperationalError
from os import path, mkdir
from collections import OrderedDict
from datetime import datetime
import numpy as np


class Database(object):

    def __init__(self, database_name="results_sequential"):

        # Backup is a database format, using Sqlite3 management system
        self.folder_path = "{}/../results".format(path.dirname(path.dirname(path.realpath(__file__))))
        self.db_path = "{}/{}.db".format(self.folder_path, database_name)
        self.table_name = None
        self.connexion = None
        self.cursor = None

        self.create_directory()

        self.types = {int: "INTEGER", float: "REAL", str: "TEXT", list: "TEXT"}

    def create_directory(self):

        if path.exists(self.folder_path):
            pass
        else:
            mkdir(self.folder_path)

    def table_exists(self, table_name):

        r = 0

        if path.exists(self.db_path):

            # noinspection SqlResolve
            already_existing = self.read("SELECT name FROM sqlite_master WHERE type='table'")

            if already_existing:

                already_existing = [i[0] for i in already_existing]

                if table_name in already_existing:

                    r = 1

        else:
            pass

        return r

    def create_table(self, table_name, columns):

        query = "CREATE TABLE `{}` (" \
                "ID INTEGER PRIMARY KEY AUTOINCREMENT, ".format(table_name)
        for key, value in columns.items():

            if value in self.types:
                v = self.types[value]
            else:
                v = "TEXT"

            query += "{} {}, ".format(key, v)

        query = query[:-2]
        query += ")"
        self.write(query)

    def fill_table(self, table_name, **kwargs):

        query = "INSERT INTO `{}` (".format(table_name)
        for i in kwargs.keys():
            query += "{}, ".format(i)

        query = query[:-2]
        query += ") VALUES("
        for j in kwargs.values():

            query += '''"{}", '''.format(j)

        query = query[:-2]
        query += ")"

        try:
            self.write(query)
        except OperationalError as e:
            print("Error with query", query)
            raise e
    
    def read(self, query):

        self.open()

        try:
            self.cursor.execute(query)
        except OperationalError as e:
            print("Error with query", query)
            raise e

        content = self.cursor.fetchall()

        self.close()

        return content

    def write(self, query):

        self.open()
        self.cursor.execute(query)
        self.close()

    def open(self):

        # Create connexion to the database
        self.connexion = connect(self.db_path)
        self.cursor = self.connexion.cursor()

    def close(self):

        # Save modifications and close connexion.
        self.connexion.commit()
        self.connexion.close()

    def empty(self, table_name):

        query = "DELETE from `{}`".format(table_name)

        self.write(query)

    def remove(self, table_name):

        query = "DROP TABLE `{}`".format(table_name)
        self.write(query)

    def read_column(self, table_name, column_name, **kwargs):
        
        if not kwargs:
            query = "SELECT {} from {}".format(column_name, table_name)
        else:

            conditions = ""
            for i, j in kwargs.items():
                conditions += "{}='{}' AND ".format(i, j)
            conditions = conditions[:-5]

            query = "SELECT {} from {} WHERE {}".format(column_name, table_name, conditions)
        
        a = self.read(query)
        # print("result query", a)
        if a:
            a = [i[0] for i in a]
            if len(a) == 1:
                a = a[0]

        return a


class BackUp(object):

    def __init__(self):

        self.db = Database()
        self.session_table = None

    def create_summary_table(self, parameters):

        if not self.db.is_table_existing("summary"):

            print("BackUp: Create 'summary' table.")

            db_columns = OrderedDict()
            db_columns["session_table_ID"] = str
            db_columns["date"] = str
            db_columns["time"] = str
            for key in parameters:
                db_columns[key] = type(parameters[key])

            self.db.create_table(table_name="summary", columns=db_columns)

        else:
            print("BackUp: I will use the 'summary' table that already exists.")

    def fill_summary_table(self, session_table, parameters):

        today = datetime.now()
        date = "{}/{}/{}".format(today.year, str(today.month).zfill(2), str(today.day).zfill(2))
        time = "{}:{}".format(str(today.hour).zfill(2), str(today.minute).zfill(2))

        self.db.fill_table(table_name="summary",
                           session_table_ID=session_table,
                           date=date,
                           time=time,
                           **parameters)

        print("BackUp: I filled the 'summary table'.")

    def create_session_table(self, data):

        if not self.db.is_table_existing(self.session_table):

            print("BackUp: Create the 'session' table.")

            db_columns = OrderedDict()
            for key in data[0]:  # data is a list of dictionaries, each of those being for one trial
                db_columns[key] = type(data[0][key])
            self.db.create_table(table_name=self.session_table, columns=db_columns)

        else:

            print("BackUp: I will use the 'session' table that already exists.")

    def fill_session_table(self, data):

        for i in range(len(data)):

            self.db.fill_table(table_name=self.session_table,
                               **data[i])

        print("BackUp: I filled the 'session' table.")

    def save(self, parameters, data):

        if data:
            self.create_summary_table(parameters)

            table_ids = self.db.read_column("summary", "session_table_ID")
            if table_ids:
                table_ids = [int(i.split("session")[1]) for i in table_ids]
                self.session_table = "session{}".format(np.max(table_ids)+1)

            else:
                self.session_table = "session1"

            self.fill_summary_table(session_table=self.session_table, parameters=parameters)
            self.create_session_table(data)

            self.fill_session_table(data)

            print("BackUp: Data saved.")
        else:
            print("BackUp: No data to save.")


if __name__ == '__main__':

    back_up = BackUp()
    # back_up.create_summary_table()
    # back_up.save()






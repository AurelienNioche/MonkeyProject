from sqlite3 import connect, OperationalError
import os
import json

from utils.utils import log


class Database(object):

    name = "Database"

    def __init__(self, database_path=None):

        if database_path is None:
            parameters_folder = os.path.abspath("{}/../parameters".format(os.path.dirname(os.path.abspath(__file__))))
            with open("{}/results_path.json".format(parameters_folder)) as file:
                param = json.load(file)

            database_folder = os.path.expanduser(param["database_folder"])
            os.makedirs(database_folder)
            self.db_path = "{}/{}".format(database_folder, param["database_name"])

        else:
            self.db_path = database_path

        self.table_name = None
        self.connexion = None
        self.cursor = None

        self.types = {int: "INTEGER", float: "REAL", str: "TEXT", list: "TEXT"}

    def table_exists(self, table_name):

        r = 0

        if os.path.exists(self.db_path):

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
            log("Database: Error with query: {}".format(query), self.name)
            raise e

    def read(self, query):

        self.open()

        try:
            self.cursor.execute(query)
        except OperationalError as e:
            log("Database: Error with query: {}".format(query), self.name)
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
            query = "SELECT {} from `{}`".format(column_name, table_name)
        else:

            conditions = ""
            for i, j in kwargs.items():
                conditions += "{}='{}' AND ".format(i, j)
            conditions = conditions[:-5]

            query = "SELECT {} from `{}` WHERE {}".format(column_name, table_name, conditions)

        a = self.read(query)

        if a:
            a = [i[0] for i in a]
            if len(a) == 1:
                a = a[0]

        return a

# %%
import mysql.connector

import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
pd.set_option('display.max_columns', None)
load_dotenv()

# %%
# Ziehe Daten aus der Datenbank

# Konstanten für Zugriff auf DB
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_TABLE = os.getenv("DB_TABLE")

mydb = mysql.connector.connect(
    host = DB_HOST,
    user = DB_USER,
    password = DB_PASSWORD,
    database = DB_DATABASE)

mycursor = mydb.cursor()
mycursor.execute(f"SELECT * FROM {DB_DATABASE}.{DB_TABLE}")
myresult = mycursor.fetchall()
mydb.close()


price_series = pd.DataFrame(myresult)#.loc[:,1]
price_series = price_series.rename({1: "diff_0"}, axis = 1)

print(price_series)

# %%
# Visualisierung

def visualization():
    diff_columns = [diff for diff in list(price_series.columns) if len(diff) == 6]
    amount_columns = len(diff_columns)
    fig, ax = plt.subplots(amount_columns)
    fig.tight_layout()
    for i, ax in enumerate(fig.axes):
        ax.plot(price_series[diff_columns].iloc[:, i])
        ax.set_title(f"{diff_columns[i]}")
        
# %% 
# main

def main():
    visualization()


# %%
# execution

if "__name__" == "__main__":
    main()
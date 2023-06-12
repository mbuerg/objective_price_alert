# Mit diesem Skript werden Preise von amazon gezogen und in einer DB gesammelt

# %%
# Module laden
# pip uninstall mysql-connector
# pip install mysql-connector-python
import pandas as pd
import mysql.connector
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# %%

# Bei RapidAPI anmelden und bei dieser API registrieren
# https://rapidapi.com/JSL346/api/amazon-product-price-data/

# man benötigt die URL der api
# Spezifikationen des Produkts, also asin und location
# host und den API Key

URL = os.getenv("URL")
ASINS = os.getenv("ASINS")
LOCALE = os.getenv("LOCALE")
QUERYSTRING = {"asins": ASINS, "locale": LOCALE}
API_HOST = os.getenv("API_HOST")
API_KEY = os.getenv("API_KEY")

# Erstelle ein dict für das request
HEADERS = {
	"X-RapidAPI-Host": API_HOST,
	"X-RapidAPI-Key": API_KEY
}

# requeste Daten
response = requests.request("GET", URL, headers = HEADERS, params = QUERYSTRING)

#print(response)


# %%
# erstelle dataframe mit Zeitpunkt und dem aktuellen Preis

price_data = pd.DataFrame({"Zeitpunkt" : [pd.to_datetime("now")],
                     response.json()[0]["product_name"] : 
                         [response.json()[0]["current_price"]]})

print(price_data)


# %%
# importiere Daten in eine DB
# Zuerst muss man eventuell einen user erstellen

# Konstanten für Zugriff auf DB
DB_HOST = os.getenv("DB_HOST")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")
TABLE = os.getenv("TABLE")


# Greife auf DB zu oder erstelle diese
try:
    mydb = mysql.connector.connect(
        host = DB_HOST,
        user = USER,
        password = PASSWORD,
        database = DATABASE
        )
    
except:
    mydb = mysql.connector.connect(
        host = DB_HOST,
        user = USER,
        password = PASSWORD
        )
    mycursor = mydb.cursor()
    mycursor.execute(f"CREATE DATABASE {DATABASE}")
    
    mydb = mysql.connector.connect(
        host = DB_HOST,
        user = USER,
        password = PASSWORD,
        database = DATABASE
        )

# rufe die table auf bzw erstelle sie, falls nicht vorhanden
try:
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM objective_price_project.prices")
    
except:
    mycursor = mydb.cursor()
    mycursor.execute(f"CREATE TABLE {DATABASE}.{TABLE} (date DATE, price FLOAT )") 
    
    mycursor = mydb.cursor()
    mycursor.execute(f"SELECT * FROM {DATABASE}.{TABLE}")

    
myresult = mycursor.fetchall()

#print(myresult) 


mycursor = mydb.cursor()
mycursor.execute(f"""INSERT INTO {DATABASE}.{TABLE} 
                 VALUES('{price_data['Zeitpunkt'][0].date()}', 
                        {price_data.iloc[0, 1]})""")

mydb.commit()
mydb.close()
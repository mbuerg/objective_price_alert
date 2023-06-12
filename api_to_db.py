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

API_URL = os.getenv("API_URL")
API_ASINS = os.getenv("API_ASINS")
API_LOCALE = os.getenv("API_LOCALE")
API_QUERYSTRING = {"asins": API_ASINS, "locale": API_LOCALE}
API_HOST = os.getenv("API_HOST")
API_KEY = os.getenv("API_KEY")

# Erstelle ein dict für das request
HEADERS = {
	"X-RapidAPI-Host": API_HOST,
	"X-RapidAPI-Key": API_KEY
}

# requeste Daten
response = requests.request("GET", API_URL, headers = HEADERS, params = API_QUERYSTRING)

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
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_TABLE = os.getenv("DB_TABLE")


# Greife auf DB zu oder erstelle diese
try:
    mydb = mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
        database = DB_DATABASE
        )
    
except:
    mydb = mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD
        )
    mycursor = mydb.cursor()
    mycursor.execute(f"CREATE DATABASE {DB_DATABASE}")
    
    mydb = mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
        database = DB_DATABASE
        )

# rufe die table auf bzw erstelle sie, falls nicht vorhanden
try:
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM objective_price_project.prices")
    
except:
    mycursor = mydb.cursor()
    mycursor.execute(f"CREATE TABLE {DB_DATABASE}.{DB_TABLE} (date DATE, price FLOAT )") 
    
    mycursor = mydb.cursor()
    mycursor.execute(f"SELECT * FROM {DB_DATABASE}.{DB_TABLE}")

    
myresult = mycursor.fetchall()

#print(myresult) 


mycursor = mydb.cursor()
mycursor.execute(f"""INSERT INTO {DB_DATABASE}.{DB_TABLE} 
                 VALUES('{price_data['Zeitpunkt'][0].date()}', 
                        {price_data.iloc[0, 1]})""")

mydb.commit()
mydb.close()
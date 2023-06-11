# Mit diesem Skript werden Preise von amazon gezogen und in einer DB gesammelt

# %%
# Module laden
# pip uninstall mysql-connector
# pip install mysql-connector-python
import pandas as pd
import mysql.connector
import requests


# %%

# Bei RapidAPI anmelden und bei dieser API registrieren
# https://rapidapi.com/JSL346/api/amazon-product-price-data/

# man benötigt die URL der api
# Spezifikationen des Produkts, also asin und location
# host und den API Key
# In diesem Beispiel handelt es sich um die Harry Potter Bücher.
# Die Auswahl dieses Beispiels hat keinen tieferen Sinn

URL = "https://amazon-product-price-data.p.rapidapi.com/product"
QUERYSTRING = {"asins":"0545162076","locale":"US"}
HOST = "amazon-product-price-data.p.rapidapi.com"
API_KEY = ""

# Erstelle ein dict für das request
HEADERS = {
	"X-RapidAPI-Host": HOST,
	"X-RapidAPI-Key": API_KEY
}

# requeste Daten
response = requests.request("GET", URL, headers = HEADERS, params = QUERYSTRING)

# response.json()  enthält alle verfügbaren Daten des Produkts zum Zeitpunkt des requests

# response output = 200, falls es geklappt hat


# %%
# erstelle dataframe mit Zeitpunkt und dem aktuellen Preis

price_data = pd.DataFrame({"Zeitpunkt" : [pd.to_datetime("now")],
                     response.json()[0]["product_name"] : 
                         [response.json()[0]["current_price"]]})

#print(price_data)


# %%
# importiere Daten in eine DB
# Zuerst muss man eventuell einen user erstellen

# Konstanten für Zugriff auf DB
HOST = ""
USER = ""
PASSWORD = ""
DATABASE = "objective_price_project"


# Greife auf DB zu oder erstelle diese
try:
    mydb = mysql.connector.connect(
        host = HOST,
        user = USER,
        password = PASSWORD,
        database = DATABASE
        )
    
except:
    mydb = mysql.connector.connect(
        host = HOST,
        user = USER,
        password = PASSWORD
        )
    mycursor = mydb.cursor()
    mycursor.execute("CREATE DATABASE objective_price_project")
    
    mydb = mysql.connector.connect(
        host = HOST,
        user = USER,
        password = PASSWORD,
        database = DATABASE
        )

# rufe die table "prices" auf bzw erstelle sie, falls nicht vorhanden
try:
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM objective_price_project.prices")
    
except:
    mycursor = mydb.cursor()
    mycursor.execute("""CREATE TABLE objective_price_project.prices (date DATE, 
                     price FLOAT )""") 
    
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM objective_price_project.prices")

    
myresult = mycursor.fetchall()

# print(myresult) 


mycursor = mydb.cursor()
mycursor.execute(f"""INSERT INTO objective_price_project.prices 
                 VALUES('{price_data['Zeitpunkt'][0].date()}', 
                        {price_data.iloc[0, 1]})""")

mydb.commit()
mydb.close()

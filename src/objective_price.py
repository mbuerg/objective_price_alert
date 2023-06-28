# %%
import mysql.connector

import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from statsmodels.tsa.stattools import adfuller
from email.message import EmailMessage
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

def get_data():
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
    return price_series

data = get_data()

#from datetime import date
#zahl = pd.DataFrame({0: [date.today()], "diff_0": [40]})
#price_series = pd.concat([price_series, zahl]) zum Testen, falls alle Werte konstanten sind
#print(price_series)


# %%
# Eventuell stationär machen, falls der p-Wert des ADF-Tests größer 5% ist
# DAbei bilden erste und zweite Differenzenfolgen quasi die erste und zweite
# Ableitung. Sind beide signifikant negativ deutet das auf ein starkes
# Fallen des Zeitreihenwertes hin, sprich der Preis ist sehr günstig im 
# Vergleich zu vergangenen Werten

# Berechne Differenzenfolgen, bis der p-Wert des ADFuller-Tests signifikant ist

def get_diffs(price_series):
    order = 1 # Ordnung der Differenzierung
    adf_test_result = adfuller(price_series.iloc[:,-1])
    while adf_test_result[1] > 0.05 and order <= 2:
        price_series[f"diff_{order}"] = price_series.iloc[:,-1].diff(1)
        price_series = price_series \
                    .fillna(price_series[f"diff_{order}"].mean())
        adf_test_result = adfuller(price_series.iloc[:,-1])
        order += 1
    price_series = price_series.set_index(0)
    return price_series

data_diffed = get_diffs(data)

# order <=2 verhindert, dass die Schleife unendlich laufen kann, des Weiteren
# wird mit jeder höheren Ordnung die Differenzenfolge schwieriger zu interpretieren
# Wenn die Ordnungen zu hoch werden ist es vermutlich sowieso anzuraten die
# Zeitreihe zunächst zu transformieren. Dieses Feature muss noch eingebaut werden.


# %%
# Tschebyscheff anwenden

# Dafür braucht man Infimum und Supremum des Intervalls
# für ein k = 4.5 lässt sich eine Wahrscheinlichkeit von höchstens ca 5% finden
# Also das Intervall ist (E(X) - 4.5*sigma, E(X) + 4.5 *sigma), wobei die 
# Wahrscheinlichkeit, dass die Realisation x außerhalb des Intervalls liegt
# höchstens 5% beträgt. Wenn x außerhalb dieses Intervalls liegt, wird dies
# als "objektiv" weit entfernt von den anderen Werten gesehen.
# Dieses Prinzip wendet man auf alle Differenzenfolgen an, also auf den 
# originalen Preis (ist der Preis niedrig im vgl zu den vorherigen Werten?),
# diff_1 (hat der Preis stark abgenommen?) und
# diff_2 (Hat sich die Abnahme von diff_1 verstärkt oder verringert?)
# Im Idealfall sind alle signifikant. 

# Streng genommen handelt es sich um ein multiples Testproblem, sodass
# man eigentlich das k in der folgenden Funktion vergrößern müsste, aber
# es handelt sich um höchstens 3 Tests, die durchgeführt werden können
# von daher kann man darauf verzichten.

# Signifkanzen auf Null setzen

def set_significance(price_series):
    for cols in range(0, price_series.shape[1]):
        price_series[f"diff_{cols}_significance"] = 0
    return price_series

data_diffed_sig = set_significance(data_diffed)

# Die Spalten für die Differenzenfolgen werden für die folgende Funktion 
# und für das Plotten benötigt

def get_diff_columns(price_series):
    return [diff for diff in list(price_series.columns) if len(diff) == 6]
 
diff_columns = get_diff_columns(data_diffed_sig)   


# Funktion zum Berechnen, ob der aktuelle Preis "objektiv günstig" ist
def calculate_tschebyscheff(price_series:"pd.Series", k:"int"=4.5, l:"int"=None) -> "pd.DataFrame":
    # k steht für die Standardabweichung, 4.5 ist default
    # l steht für die Länge der pd.Series vom aktuellsten Wert runterrechnen
    # um l Einheiten. Denn es kann Sinn machen, dass man sehr alte Werte nicht
    # betrachten will. Alle Beobachtungen sind default-Wert
    if l is None:
        l = len(price_series)
    for col in range(0, len(diff_columns)):
        mean = price_series.iloc[-l:,col].mean()
        sigma = price_series.iloc[-l:,col].std()
        infimum = mean - k*sigma
        #supremum = mean + k*sigma
        current_diff = price_series.iloc[-1,col]
        if current_diff < infimum: # or current_diff > supremum:
            price_series[f"diff_{col}_significance"].iloc[-1] = 1 # 1 heißt signifikant
    return price_series


tschebyscheff = calculate_tschebyscheff(price_series = data_diffed_sig, k = 4.5)

# print(tschebyscheff)

# %%
# Daten visualisieren

def visualization():
    amount_columns = len(diff_columns)
    fig, ax = plt.subplots(amount_columns)
    fig.tight_layout()
    for i, ax in enumerate(fig.axes):
        ax.plot(price_series[diff_columns].iloc[:, i])
        ax.set_title(f"{diff_columns[i]}")

# %%
# email verschicken, falls mindestens eine diff signifikant

def email():
    # Namen der Signifikanz-Spalten
    sig_columns = [sig for sig in list(price_series.columns) if len(sig) > 6]
    # Falls mindestens eine der Differenzenfolgen auf einen objektiv günstigen
# Preis hinweist, dann verschicke eine email.
    if tschebyscheff[sig_columns].iloc[-1].any():
        EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
        EMAIL_SERVER = os.getenv("EMAIL_SERVER")
        EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
        EMAIL_ADDRESS_REC = os.getenv("EMAIL_ADDRESS_REC")
        EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

        msg = EmailMessage()
        msg["Subject"] = "Preis ist objektiv guenstig"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS_REC
            
        msg.set_content(
            "Hallo, der Preis ist momentan objektiv niedrig mit " \
            f"${price_series['diff_0'].iloc[-1]}!")


        with smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS,
                        EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS,
                            EMAIL_ADDRESS_REC,
                            msg.as_string())

# %%
# main

def main():
    visualization()
    email()

# %%
# execute

if __name__ == "__main__":
    main()

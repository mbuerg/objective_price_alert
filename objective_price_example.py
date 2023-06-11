# %%
# import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import smtplib
from statsmodels.tsa.stattools import adfuller
from email.message import EmailMessage
pd.set_option('display.max_columns', None)

# %%
# Bitcoin Beispiel

#btc = pd.read_csv("BTC-USD.csv")
#btc["diff_0"] = btc["Adj Close"]
#price_series = btc["diff_0"] # diff_0 = price
#price_series = price_series.round(2)
#price_series = pd.DataFrame(price_series)
#print(price_series)

# %%
# Beispiel!

np.random.seed(123)
price = np.random.randint(0, 10, 100)
price_series = np.append(price, [-25, -50, -100])
price_series = pd.DataFrame({"diff_0": price_series}) # diff_0 = preis
#print(price_series)

# %%
# Testen, ob stationär

adf_test_result = adfuller(price_series["diff_0"])
#print(adf_test_result)

# %%
# Eventuell stationär machen, falls der p-Wert des ADF-Tests größer 5% ist
# DAbei bilden erste und zweite Differenzenfolgen quasi die erste und zweite
# Ableitung. Sind beide signifikant negativ deutet das auf ein starkes
# Fallen des Zeitreihenwertes hin, sprich der Preis ist sehr günstig im 
# Vergleich zu vergangenen Werten

# Berechne Differenzenfolgen, bis der p-Wert des ADFuller-Tests signifikant ist
order = 1 # Ordnung der Differenzierung
adf_test_result = adfuller(price_series.iloc[:,-1])
while adf_test_result[1] > 0.05 and order <= 2:
    price_series[f"diff_{order}"] = price_series.iloc[:,-1].diff(1)
    price_series = price_series.fillna(price_series.mean())
    adf_test_result = adfuller(price_series.iloc[:,-1])
    order += 1

#print(adf_test_result)

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
for cols in range(0, price_series.shape[1]):
    price_series[f"diff_{cols}_significance"] = 0

# Die Spalten für die Differenzenfolgen werden für die folgende Funktion 
# und für das Plotten benötigt
diff_columns = [diff for diff in list(price_series.columns) if len(diff) == 6]

# Funktion zum Berechnen, ob der aktuelle Preis "objektiv günstig" ist
def calculate_tschebyscheff(data:"pd.Series", k:"int"=4.5, l:"int"=None) -> "pd.DataFrame":
    # k steht für die Standardabweichung, 4.5 ist default
    # l steht für die Länge der pd.Series vom aktuellsten Wert runterrechnen
    # um l Einheiten. Denn es kann Sinn machen, dass man sehr alte Werte nicht
    # betrachten will. Alle Beobachtungen sind default-Wert
    if l is None:
        l = len(data)
    for col in range(0, len(diff_columns)):
        mean = data.iloc[-l:,col].mean()
        sigma = data.iloc[-l:,col].std()
        infimum = mean - k*sigma
        #supremum = mean + k*sigma
        current_diff = data.iloc[-1,col]
        # return True, falls jüngster Preis unter dem Intervall, sonst False
        if current_diff < infimum: # or current_diff > supremum:
            data[f"diff_{col}_significance"].iloc[-1] = 1 # 1 = signifikant
    return data

tschebyscheff = calculate_tschebyscheff(data = price_series, k = 4.5)
#print(tschebyscheff)

# %%
# Daten visualisieren

amount_columns = len(diff_columns)
fig, ax = plt.subplots(amount_columns)
fig.tight_layout()
for i, ax in enumerate(fig.axes):
    ax.plot(price_series[diff_columns].iloc[:, i])
    ax.set_title(f"{diff_columns[i]}")

# %%
# email verschicken, falls mindestens eine diff signifikant

# Namen der Signifikanz-Spalten
sig_columns = [sig for sig in list(price_series.columns) if len(sig) > 6]

# Falls mindestens eine der Differenzenfolgen auf einen objektiv günstigen
# Preis hinweist, dann verschicke eine email.
if tschebyscheff[sig_columns].iloc[-1].any():
    # Beispiel, falls von hotmail eine mail geschickt werden soll
    PORT = 587
    SERVER = "smtp-mail.outlook.com"
    EMAIL_ADDRESS = ""
    EMAIL_ADDRESS_REC = ""
    PASSWORD = ""

    msg = EmailMessage()
    msg["Subject"] = "Preis ist objektiv guenstig"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS_REC
        
    msg.set_content(
        "Hallo, der Preis ist momentan objektiv niedrig mit " \
        f"${price_series['diff_0'].iloc[-1]}!")


    with smtplib.SMTP(SERVER, PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS,
                     PASSWORD)
        server.sendmail(EMAIL_ADDRESS,
                        EMAIL_ADDRESS_REC,
                        msg.as_string())


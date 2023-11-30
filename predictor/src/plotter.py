"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

df = pd.read_csv('model_output_no_1.csv')
df['time_stamp'] = pd.to_datetime(df['time_stamp'], unit='s')
measured_values = df['measured']
predicted_values = df['prediction']

plt.figure(figsize=(20, 10))

plt.plot(df['time_stamp'], measured_values, label='Mért értékek',  linestyle='-', color='blue')
plt.plot(df['time_stamp'], predicted_values, label='Előrejelzett értékek', linestyle='-', color='green')

date_form = DateFormatter("%Y-%m-%d %H:%M:%S")
plt.gca().xaxis.set_major_formatter(date_form)
plt.gca().xaxis.set_major_locator(plt.MaxNLocator(nbins=10))  # Adjust the number of ticks as needed

plt.xticks(rotation=45, ha='right')
plt.xlabel('Időbélyeg')
plt.ylabel('Értékek')
plt.title('Előrejelzések és mérések az idő függvényében')
plt.legend()

plt.tight_layout()
plt.show()
"""
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

df = pd.read_csv('model_output_no_1.csv')

df['time_stamp'] = pd.to_datetime(df['time_stamp'], unit='s')

lstm_replica_count = df['lstm_replica_count']
hpa_replica_count = df['hpa_replica_count']

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(df['time_stamp'], hpa_replica_count, label='HPA Replikák száma', linestyle='-', color='blue')
ax.plot(df['time_stamp'], lstm_replica_count, label='LSTM Repikák száma', linestyle='-', color='green')

date_form = DateFormatter("%Y-%m-%d %H:%M:%S")
ax.xaxis.set_major_formatter(date_form)
ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=10))

plt.xticks(rotation=45, ha='right')

plt.xlabel('Időbélyeg')
plt.ylabel('Replikák száma')
plt.title('Replikák változása az idő függvényében')

plt.legend()

plt.tight_layout()

plt.show()
"""
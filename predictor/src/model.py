from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense

import numpy as np
import pandas as pd
import os


class PredictiveScalerLSTMModel:
    """
    LSTM háló alapú idősor-előrejelzési modell.
    """

    def __init__(self):
        """
        Modell inicializáció.
        """
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = Sequential()
        self.n_steps = 5
        self.X = None
        self.y = None
        self.build_model()

    def build_model(self):
        """
        LSTM Modell felépítése.
        """
        self.model.add(LSTM(50, activation='relu', input_shape=(self.n_steps, 1)))
        self.model.add(Dense(1))
        self.model.compile(optimizer='adam', loss='mse')

    def train(self, data):
        """
        A modell tanítása a megadott adatokon.

        Argumentumok:
            data (DataFrame): Az idősor adatok, amelyek alapján a modell tanítása történik.
        """
        values = data['values'].values.reshape(-1, 1)
        values_scaled = self.scaler.fit_transform(values)
        self.X, self.y = self.create_sequences(values_scaled)
        self.X = self.X.reshape((self.X.shape[0], self.X.shape[1], 1))
        self.model.fit(self.X, self.y, epochs=100, verbose=1)

    def predict(self, data):
        """
        Az idősor következő 5 értékének előrejelzése.

        Argumentumok:
            data (DataFrame): Az idősor utolsó `n_steps` értéke.

        Visszatérési érték:
            list: Az előre jelzett értékek.
        """
        last_sequence = data['values'].values[-self.n_steps:]
        time_stamps = data['time_stamp'].values[-self.n_steps:]
        sequence_matrix = last_sequence.reshape(1, -1)

        last_sequence_scaled = self.scaler.transform(last_sequence.reshape(-1, 1))
        last_sequence_scaled = last_sequence_scaled.reshape((1, self.n_steps, 1))
        predictions_scaled = []

        for _ in range(5):
            prediction_scaled = self.model.predict(last_sequence_scaled, verbose=0)
            predictions_scaled.append(prediction_scaled[0, 0])
            last_sequence_scaled = np.roll(last_sequence_scaled, -1)
            last_sequence_scaled[0, -1, 0] = prediction_scaled[0, 0]

        predictions = self.scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1))
        return predictions, sequence_matrix, time_stamps

    def create_sequences(self, data):
        """
        Szekvenciák létrehozása az adatokból

        Argumentumok:
            data (np.array): Az adatok, amelyekből a szekvenciák kreálódnak.

        Visszatérési érték:
            tuple: (X, y), ahol X a bemeneti szekvencia és y a cél érték.
        """
        X, y = [], []
        for i in range(len(data) - self.n_steps):
            X.append(data[i:(i + self.n_steps), 0])
            y.append(data[i + self.n_steps, 0])
        return np.array(X), np.array(y)

# Adathalmaz betöltése
df = pd.read_csv("measurements_no_1.csv")
df.columns = ['time_stamp', 'values']

# Modell létrehozása és tanítása
model = PredictiveScalerLSTMModel()
model.train(df)

# Modell mentése
model.model.save("predictive_scaler_lstm.keras", overwrite=True)

chunk_size = 5

output_file = "model_output_no_1.csv"

for chunk in pd.read_csv("measurements_no_2.csv", chunksize=chunk_size):
    try:
        chunk.columns = ['time_stamp', 'values']
        # Predikciók megcsinálása a 10-es idősor részletre
        predicted_metrics, measured_metrics, time_stamp = model.predict(chunk)
        # Kimentsük az adatok egy adatkeretbe
        average_measured = np.average(measured_metrics)
        hpa_replica_count = np.ceil(average_measured/100)
        average_predicted = np.average(predicted_metrics)
        lstm_replica_count = np.ceil(average_predicted/100)
        output = {
            'measured': measured_metrics.flatten(),
            'prediction': predicted_metrics.flatten(),
            'time_stamp': time_stamp,
            'lstm_replica_count': np.full_like(predicted_metrics, lstm_replica_count).flatten(),
            'hpa_replica_count': np.full_like(measured_metrics, hpa_replica_count).flatten()
        }

        print(output)
        
        output_df = pd.DataFrame(output)

        if os.path.exists(output_file):
            output_df.to_csv(output_file, mode='+a', header=False, index=False)
        else:
            output_df.to_csv(output_file, index=False)

        print("Output written to", output_file)
        
    except ValueError:
        break

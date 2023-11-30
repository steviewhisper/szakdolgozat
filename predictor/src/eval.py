from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model

import numpy as np
import pandas as pd

class Eval:
    def __init__(self, model_path, scaler):
        self.model_path = model_path
        self.scaler = scaler
        self.n_steps = 5

    def load_model(self):
        return load_model(self.model_path)

    def fit_scaler(self, training_data):
        self.scaler.fit(training_data['values'].values.reshape(-1, 1))

    def predict(self, data):
        model = self.load_model()

        if not self.scaler.scale_:
            raise ValueError("A skálázó nem illeszkedik")
        
        values_scaled = self.scaler.transform(data['values'].values.reshape(-1, 1))
        last_sequence_scaled = values_scaled[-self.n_steps:].reshape((1, self.n_steps, 1))

        predictions_scaled = []

        for _ in range(5):
            prediction_scaled = model.predict(last_sequence_scaled, verbose=0)
            predictions_scaled.append(prediction_scaled[0, 0])
            last_sequence_scaled = np.roll(last_sequence_scaled, -1)
            last_sequence_scaled[0, -1, 0] = prediction_scaled[0, 0]

        predictions = self.scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1))
        return predictions

saved_model_path = "predictive_scaler_lstm.keras"
scaler = MinMaxScaler(feature_range=(0, 1))
eval_model = Eval(model_path=saved_model_path, scaler=scaler)

df = pd.read_csv("measurements_no_1.csv")
df.columns = ['time_stamp', 'values']
eval_model.fit_scaler(df)

from metric_parser import parser
from eval import eval_model
from datetime import datetime
from k8 import k8_client

import pandas as pd
import numpy as np
import math
import csv


def write_to_csv(measured_values, predicted_volume, time_stamp, replicas_lstm, replicas_hpa):
    data = [measured_values, predicted_volume,time_stamp, [replicas_lstm] * len(predicted_volume), [replicas_hpa] * len(measured_values)]
    data_transposed = list(zip(*data))

    with open('model_output_no_2.csv', '+a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['measured','prediction','time_stamp','lstm_replica_count','hpa_replica_count'])
        csvwriter.writerows(data_transposed)        

while True:
    last_record = parser.return_last_sequence()
    print(last_record)
    time_stamps = [item['time_stamp'] for item in last_record]
    values = [float(item['volume']) for item in last_record]
    
    df = pd.DataFrame({
    'time_stamp': time_stamps,
    'values': values
    })

    predictions = eval_model.predict(df)
    average_predicetd = np.average(predictions)
    lstm_replica_count = np.ceil(average_predicetd/100)
    average_measured = sum(values)/len(values)
    hpa_replica_count = math.ceil(average_measured/100)

    current_rep_count = k8_client.get_current_pod_count("service-to-be-scaled")
    
    if current_rep_count < lstm_replica_count:
        k8_client.scale_up("service-to-be-scaled", int(lstm_replica_count))
    else:
        k8_client.scale_down("service-to-be-scaled", int(lstm_replica_count))
    
    write_to_csv(values, predictions.flatten(), time_stamps, lstm_replica_count, hpa_replica_count)
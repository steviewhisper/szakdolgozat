import requests
import time
import json
import csv


class Parser:
    """
    Egy osztály a Prometheusból származó adatok feldolgozására és CSV fájlba írására, vagy szimpa modellnek való átadására.

    Attribútumok:
        __STATIC__ (dict): A statikus változók szótára.

    Metódusok:
        query_request_volume(self) -> list: Lekérdezés a Prometheust a kérelemmennyiség mérőszámra.
        return_last_sequence(self) -> list: Visszaadja az utolsó öt kérelemmennyiség mérőszámot tartalmazó listát.
        write_to_csv(self) -> None: Az utolsó kérelemmennyiség mérőszám lista CSV fájlba írja.
    """

    __STATIC__ = {
        "PROMETHEUS_URL": "http://prometheus.local",
        "SEQUENCE_LENGTH": 5
    }

    def __init__(self):
        """
        Parser incializálása.
        """
        pass

    def query_request_volume(self) -> list:
        """
        Lekérdezés a Prometheust a kérelemmennyiség mérőszámra.

        Visszatérési érték:
            list: A kérelemmennyiség-metrika listája, vagy None, ha a lekérdezés sikertelen.
        """
        response = requests.get(self.__STATIC__["PROMETHEUS_URL"] + '/api/v1/query',
                                params={"query": "round(sum(irate(nginx_ingress_controller_requests{controller_pod=~'.*',controller_class=~'.*',controller_namespace=~'.*',ingress=~'service-to-be-scaled-ingress'}[2m])) by (ingress), 0.001)"})
        
        if response.status_code == 200:
            json_format = json.loads(response.text)
            result = json_format["data"]["result"]

            if len(result) > 0:
                metric_vector = result[0]["value"]
                return metric_vector if len(metric_vector) > 0 else None
        else:
            print(f"A Prometheus lekérdezés sikertelen: {response.status_code}")
            return None

    def return_last_sequence(self) -> list:
        """
        Visszaadja az utolsó öt kérelemmennyiség mérőszámot tartalmazó listát.

        Visszatérési érték:
            list: Egy lista a kérelemmennyiség mérőszámokról.
        """
        last_sequence = []

        while len(last_sequence) < self.__STATIC__["SEQUENCE_LENGTH"]:
            print("A metrikavektor lekérdezése..")
            metric_vector = self.query_request_volume()
            print("Alvás 30 másodpercig")
            time.sleep(30)

            if metric_vector:
                metric_dict = {"time_stamp": metric_vector[0], "volume": metric_vector[1]}
                print(f"Szekvencia-elem hozzáadva a listához:{metric_dict}")
                last_sequence.append(metric_dict)
                print(f"Aktuális szekvenciahoszsz: {len(last_sequence)}")

        return last_sequence

    def write_to_csv(self) -> None:
        """
        Az utolsó kérelemmennyiség mérőszám CSV fájlba írása.
        """
        metric_vector = self.query_request_volume()

        if metric_vector:
            metric_dict = {"time_stamp": metric_vector[0], "volume": metric_vector[1]}
            field_names = ["time_stamp", "volume"]

            with open('measurements_no2.csv', 'a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=field_names)
                writer.writerow(metric_dict)


parser = Parser()

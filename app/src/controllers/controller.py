from services.service import service

from prometheus_client import (
    Counter, 
    Gauge, 
    generate_latest
)
from flask_cors import cross_origin
from flask import Response
from time import time

class Controller:
    def __init__(self):
        self.service = service
        self.request_start_time = 0
        self.request_count = 0
        self.request_counter = Counter("flask_app_requests_total", "Total number of requests")
        self.response_time_gauge = Gauge("flask_app_response_time_seconds", "Average response time in seconds")

    @cross_origin()
    def index(self):
        self.request_start_time = time()
        self.request_count += 1
        self.request_counter.inc()
        try:
            return self.service.mock()
        finally:
            """ átalakítjuk ms-be a válaszidőt """
            response_time = (time() - self.request_start_time) * 1000
            formatted_response_time = "{:.2f}".format(response_time)
            self.response_time_gauge.set(formatted_response_time)

    @cross_origin()
    def metrics(self):
        return Response(generate_latest(), content_type="text/plain; version=0.0.4")


controller = Controller()

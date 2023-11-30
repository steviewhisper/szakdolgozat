from flask import Blueprint

from controllers.controller import controller


api = Blueprint('api', __name__)

api.route('/api/v1/index', methods=['GET'])(controller.index)
api.route('/api/v1/metrics', methods=['GET'])(controller.metrics)

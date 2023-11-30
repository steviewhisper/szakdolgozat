from routes.routes import api

from flask_cors import CORS
from flask import Flask


app = Flask(__name__)
app.config["DEBUG"] = True
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.register_blueprint(api, url_prefix='/')

if __name__ == '__main__':
    app.run(port=8080)

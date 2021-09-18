from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from scripts.services import user_data_service
import logging

app = Flask(__name__)

logging.basicConfig(filename='demo.log', level=logging.DEBUG)

app.register_blueprint(user_data_service.user_data_status)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

if __name__ == '__main__':
    app.run()

from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from scripts.services import user_data_service

app = Flask(__name__)

app.register_blueprint(user_data_service.user_data_status)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

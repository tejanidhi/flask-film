from flask import Flask

from flask_cors import CORS
from scripts.services import user_data_service

app = Flask(__name__)

app.register_blueprint(user_data_service.user_data_status)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

if __name__ == '__main__':
    app.run()

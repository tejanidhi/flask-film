from flask import request, Blueprint, jsonify
from scripts.core.handlers.user_data_handler import UserDetails
import json

user_data_status = Blueprint("user_data_status", __name__)


@user_data_status.route("/addUser", methods=["POST"])
def add_user():
    if request.method == "POST":
        message = {"message": "Error, Enter number"}
        status = ""
        try:
            json_string = request.get_data()
            if json_string:
                json_obj = json.loads(json_string)
                status = UserDetails().add_user_handler(json_obj)
        except Exception as e:
            print(str(e))
        if status:
            return status
        else:
            return jsonify(message), 400


@user_data_status.route("/films", methods=["GET"])
def get_films():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    header_api = None
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
            final_json, status_code = UserDetails().get_film_details(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/purchaseDetails", methods=["POST"])
def purchase_details():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                json_string = request.get_data()
                if json_string:
                    json_obj = json.loads(json_string)
                    message, status = UserDetails().insert_purchase_details(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/purchasedFilms", methods=["GET"])
def get_purchased_films():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    header_api = None
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
            final_json, status_code = UserDetails().get_purchased_films_list(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code

from flask import request, Blueprint, jsonify
from scripts.core.handlers.user_data_handler import UserDetails
import json
from werkzeug.datastructures import FileStorage
import os
from bson.objectid import ObjectId
from PIL import Image
import glob

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


@user_data_status.route("/addFilm", methods=["POST"])
def add_film_details():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().insert_film_details(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/users", methods=["GET"])
def get_users():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                final_json, status_code = UserDetails().get_user_details(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/users/purchasedFilms", methods=["GET"])
def get_purchased_users():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                final_json, status_code = UserDetails().get_purchased_user_details(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/deleteFilm", methods=["POST"])
def delete_film_details():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().delete_film_details(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/editFilm", methods=["POST"])
def edit_film_details():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().edit_film_details(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/addUpdate", methods=["POST"])
def add_update():
    status = 404
    message = {"message": "Error"}
    imagefile = None
    if request.method == "POST":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                if 'imagefile' in request.files:
                    imagefile = request.files.get('imagefile', '')
                imagefile.save(f'images/{imagefile.filename}')
                message, status = UserDetails().add_update(imagefile, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/getUpdates", methods=["GET"])
def get_updates():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
            final_json, status_code = UserDetails().get_updates(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/deleteUpdate", methods=["POST"])
def delete_update():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().delete_update(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/addCast", methods=["POST"])
def add_cast_details():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().add_cast_details(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/removeCast", methods=["POST"])
def remove_cast_details():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().remove_cast_details(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/events", methods=["POST"])
def event_details():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                json_string = request.get_data()
                if json_string:
                    json_obj = json.loads(json_string)
                    message, status = UserDetails().insert_event_details(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/films/published", methods=["GET"])
def get_published_films():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    header_api = None
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
            final_json, status_code = UserDetails().get_published_films(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/films/published/change", methods=["POST"])
def publish_unpublish_film():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().publish_unpublish_film(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/addSeries", methods=["POST"])
def add_series():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().add_series(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/getSeries", methods=["GET"])
def get_series():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                final_json, status_code = UserDetails().get_series(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/addEpisode", methods=["POST"])
def add_episode():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().add_episode(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/removeEpisode", methods=["POST"])
def remove_episode():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().remove_episode(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/removeSeries", methods=["POST"])
def remove_series():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().remove_series(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/series/published/change", methods=["POST"])
def publish_unpublish_series():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().publish_unpublish_series(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status


@user_data_status.route("/series/published", methods=["GET"])
def get_published_series():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    # header_api = None
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                final_json, status_code = UserDetails().get_published_series(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/filmsSeries", methods=["GET"])
def get_series_and_films_sorted():
    final_json = {"message": "Error in Fetching"}
    status_code = 404
    # header_api = None
    if request.method == "GET":
        try:
            if request.args['api_key']:
                header_api = request.args['api_key']
                final_json, status_code = UserDetails().get_series_and_films_sorted(header_api)
        except Exception as e:
            print(e)
        return jsonify(final_json), status_code


@user_data_status.route("/orders", methods=["POST"])
def razorpay_orders():
    status = 404
    message = {"message": "Error"}
    if request.method == "POST":
        try:
            json_string = request.get_data()
            if json_string and request.args['api_key']:
                header_api = request.args['api_key']
                json_obj = json.loads(json_string)
                message, status = UserDetails().razorpay_orders(json_obj, header_api)
        except Exception as e:
            print(e)
        return jsonify(message), status

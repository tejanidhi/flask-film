import pymongo
from flask_api import status
from flask import jsonify, Response
import secrets
from scripts.utils.MongoUtility import MongoUtility


class UserDetails:
    def __init__(self):
        # self.myclient = pymongo.MongoClient(f"mongodb://{ap.MONGO_HOST}:{ap.MONGO_PORT}/")
        self.myclient = pymongo.MongoClient(
            "mongodb+srv://root:root@cluster0.iwuxd.mongodb.net/mydatabase?retryWrites=true&w=majority")
        self.mydb = self.myclient["mydatabase"]
        self.mycol = self.mydb["user_data"]
        self.pur_details = self.mydb["user_purchase_details"]
        self.film_collec = self.mydb["film_details"]

    def add_user_handler(self, input_data):
        message = {"message": "Invalid Mobile Number"}
        status_code = status.HTTP_400_BAD_REQUEST
        number_not_found = False
        input_format = False
        try:
            if not input_data:
                message = "Error, Enter value"
                status_code = status.HTTP_400_BAD_REQUEST
            if input_data["phone_number"] != " " and len(input_data["phone_number"]) == 10 and \
                    str(input_data["phone_number"]).isdigit():
                input_format = True
            if input_format:
                for x in self.mycol.find():
                    if str(x["phone_number"]) == str(input_data["phone_number"]):
                        message["message"] = "USER EXISTS"
                        message["api_key"] = x["api_key"]
                        number_not_found = True
                        status_code = status.HTTP_200_OK
                        break
            if not number_not_found and input_format:
                while True:
                    api_key = secrets.token_urlsafe(32)
                    value, response = MongoUtility().check_api_key(api_key, "mydatabase", "user_data")
                    if not response:
                        break
                input_data["api_key"] = api_key
                self.mycol.insert_one(input_data)

                status_code = status.HTTP_200_OK
                message["message"] = "USER CREATED"
                message["api_key"] = api_key
        except Exception as e:
            print(e)
        return jsonify(message), status_code

    def get_film_details(self, header_api_key):
        message = {"message": "Resource not found"}
        api_key_list = []
        film_details_list = []
        try:
            film_details_list = []
            for x in self.film_collec.find():
                del x["_id"]
                film_details_list.append(x)
            for x in self.mycol.find():
                api_key_list.append(x["api_key"])
            if header_api_key not in api_key_list:
                return message, 404
        except Exception as e:
            print(e)
        return film_details_list, 200

    def insert_purchase_details(self, input_json, header_api):
        response_status = 404
        status_message = {"message": "Error"}
        try:
            api_list = self.get_api_key_list("mydatabase", "user_data")
            film_ids_list = self.get_film_ids("mydatabase", "film_details")
            if header_api in api_list:
                message, status = MongoUtility().check_api_key(header_api, "mydatabase",
                                                               "user_purchase_details")
                if status:
                    new_message = {"api_key": message["api_key"]}
                    status_message = {"message": "No film exists"}
                    if input_json["filmid"] in film_ids_list:
                        response_status = 200
                        status_message = {"message": "already purchased"}
                        if input_json["filmid"] not in message["filmid"]:
                            message["filmid"].append(input_json["filmid"])
                            self.pur_details.update(new_message, message)
                            status_message["message"] = "User Exists, added film"
                else:
                    if input_json["filmid"] in film_ids_list:
                        input_json["filmid"] = [input_json["filmid"]]
                        input_json["api_key"] = header_api
                        self.pur_details.insert_one(input_json)
                        status_message["message"] = "User Created"
                        response_status = 200
            else:
                status_message["message"] = "Invalid api"
        except Exception as e:
            print(e)
        return status_message, response_status

    def get_film_ids(self, database_name, collection_name):
        film_ids = list()
        try:
            for x in self.myclient[database_name] \
                    [collection_name].find():
                film_ids.append(x["filmid"])
        except Exception as e:
            print(e)
        return film_ids

    def get_api_key_list(self, database_name, collection_name):
        api_key_list = []
        try:
            for x in self.myclient[database_name][collection_name].find():
                api_key_list.append(x["api_key"])
        except Exception as e:
            print(e)
        return api_key_list

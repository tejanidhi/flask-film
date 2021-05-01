import pymongo
from flask_api import status
from flask import jsonify
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
            film_id_json, api_status = MongoUtility().check_api_key(header_api_key, "mydatabase",
                                                                    "user_purchase_details")
            for x in self.myclient["mydatabase"]["film_details"].find():
                del x["_id"]
                if film_id_json:
                    if x["filmId"] in film_id_json["filmId"]:
                        x["isPurchased"] = True
                    else:
                        x["isPurchased"] = False
                else:
                    x["isPurchased"] = False
                film_details_list.append(x)
            for x in self.myclient["mydatabase"]["user_data"].find():
                api_key_list.append(x["api_key"])
            if header_api_key not in api_key_list or len(film_details_list) == 0:
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
                    if input_json["filmId"] in film_ids_list:
                        response_status = 200
                        status_message = {"message": "already purchased"}
                        if input_json["filmId"] not in message["filmId"]:
                            message["filmId"].append(input_json["filmId"])
                            self.pur_details.update(new_message, message)
                            status_message["message"] = "User Exists, added film"
                else:
                    if input_json["filmId"] in film_ids_list:
                        input_json["filmId"] = [input_json["filmId"]]
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
                film_ids.append(x["filmId"])
        except Exception as e:
            print(e)
        return film_ids

    def get_film_names(self, database_name, collection_name):
        film_names = list()
        try:
            for x in self.myclient[database_name] \
                    [collection_name].find():
                film_names.append(x["name"])
        except Exception as e:
            print(e)
        return film_names

    def get_api_key_list(self, database_name, collection_name):
        api_key_list = []
        try:
            for x in self.myclient[database_name][collection_name].find():
                api_key_list.append(x["api_key"])
        except Exception as e:
            print(e)
        return api_key_list

    def get_purchased_films_list(self, header_api):
        new_films_list = []
        message = {"message": "No films purcahsed"}
        try:
            films_list, status = self.get_film_details(header_api)
            if len(films_list) > 0:
                for each_value in films_list:
                    if each_value["isPurchased"]:
                        new_films_list.append(each_value)
            if not new_films_list:
                return message, 404
        except Exception as e:
            print(e)
        return new_films_list, 200

    def insert_film_details(self, input_json):
        message = ""
        status = 404
        try:
            film_name = input_json["name"]
            film_name_list = self.get_film_names("mydatabase", "film_details")
            if film_name not in film_name_list:
                if "cast" in input_json and "desc" in input_json \
                        and "genre" in input_json and "image" in input_json and "name" in input_json and "price" in input_json and \
                        "url" in input_json:
                    film_id = MongoUtility().get_sequence("messages")
                    input_json["filmId"] = film_id
                    self.film_collec.insert_one(input_json)
                    message = "Film details Inserted Successfully"
                    status = 200
                else:
                    message = "input data not sufficient"
            else:
                message = "Film already Exists"
        except Exception as e:
            print(e)
        return message, status

    def get_user_details(self):
        user_details_list = []
        try:
            for x in self.mycol.find():
                temp_dict = {}
                temp_dict["phone_number"] = x["phone_number"]
                temp_dict["id"] = str(x["_id"])
                user_details_list.append(temp_dict)
        except Exception as e:
            print(e)
        return user_details_list, 200


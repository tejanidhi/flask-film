import pymongo
from flask_api import status
from flask import jsonify
import secrets
from scripts.utils.MongoUtility import MongoUtility
import calendar
import time
from bson.objectid import ObjectId
import boto3
from boto3.s3.transfer import S3Transfer
import os
from PIL import Image


class UserDetails:
    def __init__(self):
        # self.myclient = pymongo.MongoClient(f"mongodb://{ap.MONGO_HOST}:{ap.MONGO_PORT}/")
        self.myclient = pymongo.MongoClient(
            "mongodb+srv://root:root@cluster0.iwuxd.mongodb.net/mydatabase?retryWrites=true&w=majority")
        self.mydb = self.myclient["mydatabase"]
        self.mycol = self.mydb["user_data"]
        self.pur_details = self.mydb["user_purchase_details"]
        self.film_collec = self.mydb["film_details"]
        self.update_coll = self.mydb["updates"]
        self.cast_coll = self.mydb["cast_details"]

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
                ts = calendar.timegm(time.gmtime())
                input_data["created_date"] = ts
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
            # print(film_id_json, "--")
            for x in self.myclient["mydatabase"]["film_details"].find():
                # del x["_id"]
                cast_details_list = []
                if x["cast_ids"]:
                    for each_cast in x["cast_ids"]:
                        cast_details_list = []
                        for y in self.cast_coll.find({'_id': ObjectId(each_cast)}):
                            del y["_id"]
                            y["cast"]["id"] = each_cast
                            cast_details_list.append(y["cast"])
                x["cast_details"] = cast_details_list
                del x["cast_ids"]
                # print(film_id_json, str(x["_id"]))
                if film_id_json:
                    if str(x["_id"]) in film_id_json["id"]:
                        x["isPurchased"] = True
                    else:
                        x["isPurchased"] = False
                else:
                    x["isPurchased"] = False
                x["id"] = str(x["_id"])
                del x["_id"]
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
            final_json = {}
            if header_api in api_list:
                message, status = MongoUtility().check_api_key(header_api, "mydatabase",
                                                               "user_purchase_details")
                if input_json["id"] in film_ids_list:
                    if status:
                        new_message = {"api_key": header_api}
                        final_json["api_key"] = header_api
                        if input_json["id"] in message["id"]:
                            response_status = 200
                            status_message = {"message": "already purchased"}
                        elif input_json["id"] not in message["id"]:
                            message["id"].append(input_json["id"])
                            final_json["id"] = message["id"]
                            self.pur_details.update(new_message, final_json)
                            status_message["message"] = "User Exists, added film"
                    else:
                        if input_json["id"] in film_ids_list:
                            input_json["id"] = [input_json["id"]]
                            input_json["api_key"] = header_api
                            self.pur_details.insert_one(input_json)
                            status_message["message"] = "User Created"
                            response_status = 200
                else:
                    status_message["message"] = "No Film Exists"
            else:
                status_message["message"] = "Invalid api"
        except Exception as e:
            print(e)
            print(status_message, response_status)
        return status_message, response_status

    def get_film_ids(self, database_name, collection_name):
        film_ids = list()
        try:
            for x in self.myclient[database_name] \
                    [collection_name].find():
                film_ids.append(str(x["_id"]))
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
        message = {"message": "No films purchased"}
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
                    input_json["cast_ids"] = list()
                    for each_cast in input_json["cast"]:
                        get_id = self.cast_coll.insert_one(each_cast)
                        input_json["cast_ids"].append(str(get_id.inserted_id))
                    del input_json["cast"]
                    ts = calendar.timegm(time.gmtime())
                    input_json["created_date"] = ts
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
                temp_dict["created_date"] = x["created_date"]
                user_details_list.append(temp_dict)
        except Exception as e:
            print(e)
        return user_details_list, 200

    def get_purchased_user_details(self):
        user_purchase_details_list = []
        try:
            for x in self.mycol.find():
                temp_dict = {"phone_number": x["phone_number"], "id": str(x["_id"])}
                film_id_json, api_status = MongoUtility().check_api_key(x["api_key"], "mydatabase",
                                                                        "user_purchase_details")
                if api_status and film_id_json:
                    temp_dict["purchased_films"] = film_id_json["id"]
                user_purchase_details_list.append(temp_dict)
        except Exception as e:
            print(e)
        return user_purchase_details_list, 200

    def delete_film_details(self, input_json):
        message = {"message": "No Film Exists"}
        status = 200
        try:
            id = input_json["id"]
            for x in self.film_collec.find({"_id": ObjectId(id)}):
                if x:
                    self.film_collec.delete_one({"_id": ObjectId(id)})
                    message["message"] = "Deleted Succesfully"
                    status = 200
        except Exception as e:
            print(e)
        return message, status

    def edit_film_details(self, input_json):
        message = {"message": "No Film Exists"}
        status = 200
        form_json = {}
        try:
            id = None
            if "id" in input_json:
                id = input_json["id"]
            for x in self.film_collec.find({"_id": ObjectId(id)}):
                if "desc" in input_json:
                    form_json["desc"] = input_json["desc"]
                else:
                    form_json["desc"] = x["desc"]
                if "genre" in input_json:
                    form_json["genre"] = input_json["genre"]
                else:
                    form_json["genre"] = x["genre"]
                if "image" in input_json:
                    form_json["image"] = input_json["image"]
                else:
                    form_json["image"] = x["image"]
                if "name" in input_json:
                    form_json["name"] = input_json["name"]
                else:
                    form_json["name"] = x["name"]
                if "price" in input_json:
                    form_json["price"] = input_json["price"]
                else:
                    form_json["price"] = x["price"]
                if "url" in input_json:
                    form_json["url"] = input_json["url"]
                else:
                    form_json["url"] = x["url"]
                form_json["created_date"] = x["created_date"]
                form_json["cast_ids"] = x["cast_ids"]
                self.film_collec.update(x, form_json)
                message["message"] = "Edited Succesfully"
                status = 200
        except Exception as e:
            print(e)
        return message, status

    def add_update(self, imagefile):
        message = {'message': "Upload failed"}
        status = 404
        final_json = {}
        try:
            print(type(imagefile))
            transfer = S3Transfer(boto3.client('s3',
                                               aws_access_key_id='AKIAVWWSCFPVLSPN3W7W',
                                               aws_secret_access_key='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'))
            bucket = 'filmnagar-images'
            try:
                transfer.upload_file(f'images/{imagefile.filename}', bucket,
                                     key="updates" + "/" + imagefile.filename,
                                     extra_args={'ACL': 'public-read'})
            except Exception as e:
                print(e)
            url = "https://%s.s3.ap-south-1.amazonaws.com/%s" % (bucket, "updates" + "/" + imagefile.filename)
            ts = calendar.timegm(time.gmtime())
            os.remove(f'images/{imagefile.filename}')
            final_json['image_name'] = imagefile.filename
            final_json['url'] = url
            final_json['created_date'] = ts
            self.update_coll.insert_one(final_json)
            status = 200
            message['message'] = 'Updated added successfully'
            message['url'] = url
        except Exception as e:
            print(e)
        return message, status

    def get_updates(self):
        status_code = 404
        message = {"message": "No Updates"}
        output_list = []
        try:
            for x in self.update_coll.find():
                del x["_id"]
                output_list.append(x)
            if not output_list:
                return message, status_code
        except Exception as e:
            print(e)
        return output_list, 200

    def delete_update(self, input_json):
        status_code = 404
        message = {"message": "Error in Deleting"}
        try:
            delete_id = input_json["id"]
            url_to_del = ""
            for x in self.update_coll.find({"_id": ObjectId(delete_id)}):
                url_to_del = x["image_name"]
            if url_to_del:
                self.update_coll.delete_one({'_id': ObjectId(delete_id)})
                s3 = boto3.resource(
                    service_name='s3',
                    region_name='ap-south-1',
                    aws_access_key_id='AKIAVWWSCFPVLSPN3W7W',
                    aws_secret_access_key='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'
                )
                obj = s3.Object("filmnagar-images", key="updates" + "/" + url_to_del)
                obj.delete()
                status_code = 200
                message["message"] = "Deleted Update"
        except Exception as e:
            print(e)
        return message, status_code

    def add_cast_details(self, input_json):
        out_json = {}
        status_code = 404
        message = {"message": "Error in Adding Cast"}
        try:
            if input_json["filmid"] and input_json["image"] and input_json["name"] and input_json["role"]:
                out_json["image"] = input_json["image"]
                out_json["name"] = input_json["name"]
                out_json["role"] = input_json["role"]
                if out_json:
                    inserted_status = self.cast_coll.insert_one(out_json)
                    get_ins_id = inserted_status.inserted_id
                    for x in self.film_collec.find({"_id": ObjectId(input_json["filmid"])}):
                        temp_cast_ids = x["cast_ids"]
                        temp_cast_ids.append(str(get_ins_id))
                        self.film_collec.update_one({"_id": ObjectId(input_json["filmid"])},
                                                    {"$set": {"cast_ids": temp_cast_ids}})
                        message["message"] = "cast Added"
                        status_code = 200
        except Exception as e:
            print(e)
        return message, status_code

    def remove_cast_details(self, input_json):
        get_id = ""
        status_code = 404
        message = {"message": "Error in Removing Cast"}
        try:
            if input_json["id"]:
                get_id = input_json["id"]
            if get_id:
                for x in self.film_collec.find({"_id": ObjectId(input_json["filmid"])}):
                    temp_cast_ids = x["cast_ids"]
                    if get_id in temp_cast_ids:
                        temp_cast_ids.remove(get_id)
                        self.film_collec.update_one({"_id": ObjectId(input_json["filmid"])},
                                                    {"$set": {"cast_ids": temp_cast_ids}})
                        self.cast_coll.delete_one({'_id': ObjectId(get_id)})
                        message["message"] = "cast Removed"
                        status_code = 200
        except Exception as e:
            print(e)
        return message, status_code

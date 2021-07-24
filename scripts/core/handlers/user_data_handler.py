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
import uuid
from PIL import Image
import razorpay


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
        self.events_coll = self.mydb["events"]
        self.series_coll = self.mydb["series"]
        self.response_coll = self.mydb["order_response"]
        self.unique_id_list = []
        self.api_list = self.get_api_key_list("mydatabase", "user_data")

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
        status_code = 404
        film_details_list = []
        try:
            if header_api_key in self.api_list:
                film_details_list = []
                # film_id_json, api_status = MongoUtility().check_api_key(header_api_key, "mydatabase",
                #                                                         "user_purchase_details")
                for x in self.myclient["mydatabase"]["film_details"].find():
                    # del x["_id"]
                    cast_details_list = []
                    if x["cast_ids"]:
                        for each_cast in x["cast_ids"]:
                            cast_details_list = []
                            for y in self.cast_coll.find({'_id': ObjectId(each_cast)}):
                                y["id"] = str(y["_id"])
                                del y["_id"]
                                cast_details_list.append(y)
                    x["cast_details"] = cast_details_list
                    del x["cast_ids"]
                    # print(film_id_json, str(x["_id"]))
                    film_id_list = []
                    # if film_id_json:
                    #     for each_value in film_id_json["id"]:
                    #         if "filmid" in each_value:
                    #             film_id_list.append(each_value["filmid"])
                    #     if str(x["_id"]) in film_id_list:
                    #         x["isPurchased"] = True
                    #     else:
                    #         x["isPurchased"] = False
                    # else:
                    #     x["isPurchased"] = False
                    # if "isPublished" not in x:
                    #     x["isPublished"] = False
                    x["id"] = str(x["_id"])
                    del x["_id"]
                    film_details_list.append(x)
                if len(film_details_list) == 0:
                    message["message"] = "No Films Exists"
                    status_code = 200
                    return message, status_code
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return film_details_list, status_code

    def series_ids_ids(self, database_name, collection_name):
        series_ids = list()
        try:
            for x in self.myclient[database_name] \
                    [collection_name].find():
                series_ids.append(str(x["_id"]))
        except Exception as e:
            print(e)
        return series_ids

    def insert_purchase_details(self, input_json, header_api):
        response_status = 404
        status_message = {"message": "Error"}
        try:
            # api_list = self.get_api_key_list("mydatabase", "user_data")
            film_ids_list = self.get_film_ids("mydatabase", "film_details")
            series_ids_list = self.series_ids_ids("mydatabase", "series")
            final_json = {}
            if header_api in self.api_list:
                message, status = MongoUtility().check_api_key(header_api, "mydatabase",
                                                               "user_purchase_details")
                purchased_id_list = []
                # print(message, status)
                if status:
                    if "id" in message:
                        for each_value in message["id"]:
                            if "sid" in each_value:
                                purchased_id_list.append(each_value["sid"])
                            if "filmid" in each_value:
                                purchased_id_list.append(each_value["filmid"])
                # print(purchased_id_list)
                if "filmid" in input_json:
                    if input_json["filmid"] in film_ids_list:
                        if status:
                            new_message = {"api_key": header_api}
                            final_json["api_key"] = header_api
                            if input_json["filmid"] in purchased_id_list:
                                response_status = 200
                                status_message = {"message": "already purchased"}
                            elif input_json["filmid"] not in purchased_id_list:
                                if "razorpay_payment_id" in input_json and "razorpay_order_id" in input_json \
                                        and "razorpay_signature" in input_json:
                                    temp_json = {"filmid": input_json["filmid"],
                                                 "razorpay_payment_id": input_json["razorpay_payment_id"],
                                                 "razorpay_order_id": input_json["razorpay_order_id"],
                                                 "razorpay_signature": input_json["razorpay_signature"]
                                                 }
                                    message["id"].append(temp_json)
                                    final_json["id"] = message["id"]
                                    self.pur_details.update(new_message, final_json)
                                    status_message["message"] = "User Exists, added series"
                                    for x in self.film_collec.find({"_id": ObjectId(input_json["filmid"])}):
                                        x["isPurchased"] = True
                                        self.film_collec.update({"_id": ObjectId(input_json["filmid"])}, x)

                                else:
                                    status_message["message"] = "Insufficient Input"
                                    response_status = 404
                        else:
                            if input_json["filmid"] in film_ids_list:
                                temp_json = {}
                                temp_json["api_key"] = header_api
                                if "razorpay_payment_id" in input_json and "razorpay_order_id" in input_json \
                                        and "razorpay_signature" in input_json:
                                    temp_json["id"] = [{"filmid": input_json["filmid"],
                                                                           "razorpay_payment_id": input_json[
                                                                               "razorpay_payment_id"],
                                                                           "razorpay_order_id": input_json[
                                                                               "razorpay_order_id"],
                                                                           "razorpay_signature": input_json[
                                                                               "razorpay_signature"]}]
                                    self.pur_details.insert_one(temp_json)
                                    status_message["message"] = "User Created, added payment details"
                                    response_status = 200
                                    for x in self.film_collec.find({"_id": ObjectId(input_json["filmid"])}):
                                        x["isPurchased"] = True
                                        self.film_collec.update({"_id": ObjectId(input_json["filmid"])}, x)
                                else:
                                    status_message["message"] = "Insufficient Input"
                                    response_status = 404
                    else:
                        status_message["message"] = "No Film Exists"
                if "sid" in input_json:
                    if input_json["sid"] in series_ids_list:
                        if status:
                            new_message = {"api_key": header_api}
                            final_json["api_key"] = header_api
                            if input_json["sid"] in purchased_id_list:
                                response_status = 200
                                status_message = {"message": "already purchased"}
                            elif input_json["sid"] not in purchased_id_list:
                                if "razorpay_payment_id" in input_json and "razorpay_order_id" in input_json \
                                                                        and "razorpay_signature" in input_json:
                                    temp_json = {"sid": input_json["sid"],
                                                 "razorpay_payment_id": input_json["razorpay_payment_id"],
                                                 "razorpay_order_id": input_json["razorpay_order_id"],
                                                 "razorpay_signature": input_json["razorpay_signature"]
                                                 }
                                    message["id"].append(temp_json)
                                    final_json["id"] = message["id"]
                                    self.pur_details.update(new_message, final_json)
                                    status_message["message"] = "User Exists, added series"
                                    response_status = 200
                                    for x in self.series_coll.find({"_id": ObjectId(input_json["sid"])}):
                                        x["isPurchased"] = True
                                        print(x)
                                        self.series_coll.update({"_id": ObjectId(input_json["sid"])}, x)
                                else:
                                    status_message["message"] = "Insufficient Input"
                                    response_status = 404
                        else:
                            if input_json["sid"] in series_ids_list:
                                temp_json = {}
                                temp_json["api_key"] = header_api
                                if "razorpay_payment_id" in input_json and "razorpay_order_id" in input_json \
                                    and "razorpay_signature" in input_json:
                                    temp_json["id"] = [{"sid": input_json["sid"],
                                                                "razorpay_payment_id": input_json["razorpay_payment_id"],
                                                                "razorpay_order_id": input_json["razorpay_order_id"],
                                                                "razorpay_signature": input_json["razorpay_signature"]}]
                                    self.pur_details.insert_one(temp_json)
                                    status_message["message"] = "User Created, added payment details"
                                    response_status = 200
                                    for x in self.series_coll.find({"_id": ObjectId(input_json["sid"])}):
                                        x["isPurchased"] = True
                                        print(x)
                                        self.film_collec.update({"_id": ObjectId(input_json["sid"])}, x)
                                else:
                                    status_message["message"] = "Insufficient Input"
                                    response_status = 404

                    else:
                        status_message["message"] = "No Series Exists"
            else:
                status_message["message"] = "Invalid api"
        except Exception as e:
            print(e)
            # print(status_message, response_status)
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

    def insert_film_details(self, input_json, header_api):
        message = {"message": "Error in adding"}
        status = 404
        try:
            # film_name = input_json["name"]
            # film_name_list = self.get_film_names("mydatabase", "film_details")
            if header_api in self.api_list:
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
                    input_json["isPurchased"] = False
                    self.film_collec.insert_one(input_json)
                    message["message"] = "Film details Inserted Successfully"
                    status = 200
                else:
                    message["message"] = "input data not sufficient"
            else:
                message["message"] = "Authentication Failed"
                status = 401
        except Exception as e:
            print(e)
        return message, status

    def get_user_details(self, header_api):
        user_details_list = []
        message = {"message": "Authentication Failed"}
        status_code = 404
        try:
            if header_api in self.api_list:
                for x in self.mycol.find():
                    temp_dict = {}
                    temp_dict["phone_number"] = x["phone_number"]
                    temp_dict["id"] = str(x["_id"])
                    temp_dict["created_date"] = x["created_date"]
                    user_details_list.append(temp_dict)
                if user_details_list:
                    status_code = 200
                else:
                    message["message"] = "No Users found"
                    return message, status_code
            else:
                return message, status_code
        except Exception as e:
            print(e)
        return user_details_list, status_code

    def get_purchased_user_details(self, header_api):
        user_purchase_details_list = []
        message = {"message": "Authentication Failed"}
        status_code = 404
        try:
            if header_api in self.api_list:
                for x in self.mycol.find():
                    temp_dict = {"phone_number": x["phone_number"], "id": str(x["_id"])}
                    film_id_json, api_status = MongoUtility().check_api_key(x["api_key"], "mydatabase",
                                                                            "user_purchase_details")
                    if api_status and film_id_json:
                        temp_dict["purchased_films"] = film_id_json["id"]
                    user_purchase_details_list.append(temp_dict)
                if user_purchase_details_list:
                    status_code = 200
                else:
                    message["message"] = "No Purchased Users found"
                    return message, status_code
            else:
                return message, status_code
        except Exception as e:
            print(e)
        return user_purchase_details_list, status_code

    def delete_film_details(self, input_json, header_api):
        message = {"message": "No Film Exists"}
        status = 404
        try:
            if header_api in self.api_list:
                id = input_json["id"]
                for x in self.film_collec.find({"_id": ObjectId(id)}):
                    if x:
                        self.film_collec.delete_one({"_id": ObjectId(id)})
                        message["message"] = "Deleted Succesfully"
                        status = 200
            else:
                message["message"] = "Authentication Failed"
                status = 401
        except Exception as e:
            print(e)
        return message, status

    def edit_film_details(self, input_json, header_api):
        message = {"message": "No Film Exists"}
        status = 200
        form_json = {}
        try:
            if header_api in self.api_list:
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
            else:
                message["message"] = "Authentication Failed"
                status = 401
        except Exception as e:
            print(e)
        return message, status

    def add_update(self, imagefile, header_api):
        message = {'message': "Upload failed"}
        status = 404
        final_json = {}
        try:
            # print(type(imagefile))
            if header_api in self.api_list:
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
            else:
                message["message"] = "Authentication Failed"
                status = 401
        except Exception as e:
            print(e)
        return message, status

    def get_updates(self, header_api):
        status_code = 404
        message = {"message": "No Updates"}
        output_list = []
        try:
            if header_api in self.api_list:
                for x in self.update_coll.find():
                    del x["_id"]
                    output_list.append(x)
                if not output_list:
                    return message, status_code
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return output_list, status_code

    def delete_update(self, input_json, header_api):
        status_code = 404
        message = {"message": "No such Update"}
        try:
            if header_api in self.api_list:
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
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def add_cast_details(self, input_json, header_api):
        out_json = {}
        status_code = 404
        message = {"message": "Error in Adding Cast"}
        try:
            if header_api in self.api_list:
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
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def remove_cast_details(self, input_json, header_api):
        get_id = ""
        status_code = 404
        message = {"message": "Error in Removing Cast"}
        try:
            if header_api in self.api_list:
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
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def insert_event_details(self, input_json, header_api):
        status_code = 404
        message = {"message": "Error in Inserting"}
        out_json = dict()
        try:
            if header_api in self.api_list:
                if input_json["event_name"] == "PLAY_CLICKED" or input_json["event_name"] == "FILM_CLICKED" \
                        or input_json["event_name"] == "BUY_CLICKED":
                    if "event_name" in input_json and "param1" in input_json and "param2" in input_json:
                        out_json['event_name'] = input_json["event_name"]
                        out_json['param1'] = input_json["param1"]
                        out_json['param2'] = input_json["param2"]
                        ts = calendar.timegm(time.gmtime())
                        out_json['created_date'] = ts
                        if header_api:
                            for x in self.mycol.find({"api_key": header_api}):
                                out_json["userid"] = str(x["_id"])
                        if out_json:
                            self.events_coll.insert_one(out_json)
                            status_code = 200
                            message["message"] = "Inserted successfully"
                    else:
                        message["message"] = "Error in input"
                else:
                    message["message"] = "No such event"
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def get_published_films(self, header_api):
        get_films_list = []
        message = {"message": "No published films"}
        status_code = 404
        flag = False
        try:
            if header_api in self.api_list:
                get_films_list, status_code = self.get_film_details(header_api)
                if "isPublished" in get_films_list[0]:
                    if get_films_list[0]["isPublished"]:
                        flag = True
                if not flag:
                    return message, status_code
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return get_films_list, status_code

    def publish_unpublish_film(self, input_json, header_api):
        message = {"message": "Error in publishing Film"}
        status_code = 404
        try:
            if header_api in self.api_list:
                if "filmid" in input_json and "isPublished" in input_json:
                    self.film_collec.update_one({"_id": ObjectId(input_json["filmid"])},
                                                {"$set": {"isPublished": input_json["isPublished"]}})
                if input_json["isPublished"]:
                    message["message"] = "Published Film"
                else:
                    message["message"] = "Unpublished Film"
                    status_code = 200
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def add_series(self, input_json, header_api):
        message = {"message": "Error in adding series"}
        status_code = 404
        out_json = {}
        episodes_list = []
        try:
            if header_api in self.api_list:
                if "series" in input_json:
                    out_json["series"] = input_json["series"]
                if "image" in input_json:
                    out_json["image"] = input_json["image"]
                ts = calendar.timegm(time.gmtime())
                out_json["created_date"] = ts
                out_json["isPurchased"] = False
                if "episodes" in input_json:
                    for each_value in input_json["episodes"]:
                        get_uuid = self.create_unique_uuid(self.unique_id_list)
                        if get_uuid:
                            # print(get_uuid)
                            temp_json = {"episode_name": each_value, "id": get_uuid}
                            episodes_list.append(temp_json)
                out_json["episodes"] = episodes_list
                if out_json:
                    self.series_coll.insert_one(out_json)
                    message["message"] = "Added series"
                    status_code = 200
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def create_unique_uuid(self, unique_id_list):
        get_uuid = ""
        try:
            while True:
                get_uuid = str(uuid.uuid1())
                if get_uuid not in unique_id_list:
                    unique_id_list.append(get_uuid)
                    break
                else:
                    continue
        except Exception as e:
            print(e)
        return get_uuid

    def get_series(self, header_api):
        message = {"message": "Added series"}
        status_code = 404
        output_list = []
        try:
            if header_api in self.api_list:
                for x in self.series_coll.find():
                    temp_id = str(x["_id"])
                    del x["_id"]
                    x["sid"] = temp_id
                    if not x["episodes"]:
                        del x["episodes"]
                    output_list.append(x)
                if output_list:
                    message["message"] = "Added series"
                    status_code = 200
                else:
                    return message, status_code
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
                return message, status_code
        except Exception as e:
            print(e)
        return output_list, status_code

    def add_episode(self, input_json, header_api):
        id_list = []
        message = {"message": "Error in adding episode"}
        status_code = 404
        try:
            if header_api in self.api_list:
                if "sid" in input_json and "episode_name" in input_json:
                    for x in self.series_coll.find({"_id": ObjectId(input_json["sid"])}):
                        for each_value in x["episodes"]:
                            id_list.append(each_value["id"])
                        get_uuid = self.create_unique_uuid(id_list)
                        if get_uuid:
                            ts = calendar.timegm(time.gmtime())
                            temp_json = {"episode_name": input_json["episode_name"], "id": get_uuid,
                                         "created_date": ts}
                            x["episodes"].append(temp_json)
                            # print(x["episodes"])
                            self.series_coll.update_one({"_id": ObjectId(input_json["sid"])},
                                                        {"$set": {"episodes": x["episodes"]}})
                            message["message"] = "Added Episode"
                            status_code = 200
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def remove_episode(self, input_json, header_api):
        message = {"message": "Error in removing episode"}
        status_code = 404
        try:
            if header_api in self.api_list:
                if "eid" in input_json and "sid" in input_json:
                    for x in self.series_coll.find({"_id": ObjectId(input_json["sid"])}):
                        for each_document in x["episodes"]:
                            if each_document["id"] == input_json["eid"]:
                                x["episodes"].remove(each_document)
                                self.series_coll.update_one({"_id": ObjectId(input_json["sid"])},
                                                            {"$set": {"episodes": x["episodes"]}})
                                message["message"] = "Removed Episode"
                                status_code = 200
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def remove_series(self, input_json, header_api):
        message = {"message": "Error in removing series"}
        status_code = 404
        try:
            if header_api in self.api_list:
                if "sid" in input_json:
                    self.series_coll.delete_one({"_id": ObjectId(input_json["sid"])})
                    message["message"] = "Removed Series"
                    status_code = 200
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def publish_unpublish_series(self, input_json, header_api):
        message = {"message": "Error in publishing Series"}
        status_code = 404
        try:
            if header_api in self.api_list:
                if "sid" in input_json and "isPublished" in input_json:
                    self.series_coll.update_one({"_id": ObjectId(input_json["sid"])},
                                                {"$set": {"isPublished": input_json["isPublished"]}})
                if input_json["isPublished"]:
                    message["message"] = "Published Film"
                else:
                    message["message"] = "Unpublished Film"
                    status_code = 200
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
        except Exception as e:
            print(e)
        return message, status_code

    def get_published_series(self, header_api):
        get_series_list = []
        message = {"message": "No published series"}
        status_code = 404
        flag = False
        try:
            if header_api in self.api_list:
                for x in self.series_coll.find():
                    if x["isPublished"]:
                        flag = True
                        temp_id = str(x["_id"])
                        x["sid"] = temp_id
                        del x["_id"]
                        get_series_list.append(x)
                if get_series_list:
                    status_code = 200
                if not flag:
                    return message, 200
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
                return message, status_code
        except Exception as e:
            print(e)
        return get_series_list, status_code

    def get_series_and_films_sorted(self, header_api):
        message = {"message": "Unable to Fetch"}
        status_code = 404
        new_films_series = []
        try:
            if header_api in self.api_list:
                get_films, status_films = self.get_film_details(header_api)
                get_series, status_series = self.get_series(header_api)
                if get_films and get_films:
                    films_series = get_series + get_films
                    new_films_series = sorted(films_series, key=lambda k: k['created_date'])
                    status_code = 200
                else:
                    return message, status_code
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
                return message, status_code
        except Exception as e:
            print(e)
        return new_films_series, status_code

    def get_order_response_list(self):
        response_list = []
        try:
            for x in self.response_coll.find():
                response_list.append(x["receipt"])
        except Exception as e:
            print(e)
        return response_list

    def razorpay_orders(self, input_json, header_api):
        message = {"message": "Unable to create order"}
        status_code = 404
        try:
            if header_api in self.api_list:
                client = razorpay.Client(auth=("rzp_live_KuxeaJ2PlY5Aco", "uvbmKmikoju8lhQb30vkKKRc"))
                if "amount" in input_json and "currency" in input_json:
                    order_amount = input_json["amount"]
                    order_currency = input_json["currency"]
                    get_unique_id_list = self.get_order_response_list()
                    while True:
                        get_uuid = str(uuid.uuid1())
                        if get_uuid not in get_unique_id_list:
                            break
                        else:
                            continue
                    if "notes" in input_json:
                        notes = input_json["notes"]
                    else:
                        notes = ""
                    try:
                        response = client.order.create(
                            dict(amount=order_amount, currency=order_currency, receipt=get_uuid, notes=notes))
                        if response:
                            return response, 200
                    except Exception as e:
                        print(e)
                else:
                    message["message"] = "Insufficient Input"
                    return message, status_code
            else:
                message["message"] = "Authentication Failed"
                status_code = 401
                return message, status_code
        except Exception as e:
            print(e)




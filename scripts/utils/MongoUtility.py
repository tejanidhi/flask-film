import pymongo


class MongoUtility:
    def __init__(self):
        self.myclient = pymongo.MongoClient(
            "mongodb+srv://root:root@cluster0.iwuxd.mongodb.net/mydatabase?retryWrites=true&w=majority")
        self.mydb = self.myclient["mydatabase"]
        self.mycol = self.mydb["user_data"]
        self.msgcoll = self.mydb["messages"]

    def check_api_key(self, api_key, database_name, collection_name):
        flag = False
        value = {}
        try:
            for x in self.myclient[database_name]\
                    [collection_name].find({"api_key": api_key}):
                if x:
                    # del x["_id"]
                    flag = True
                    if "id" in x:
                        value["id"] = x["id"]
        except Exception as e:
            print(e)
        return value, flag

    def insert_one(self, input_json):
        try:
            mongo_response = self.mycol.insert_one(input_json)
            return mongo_response.inserted_id
        except Exception as e:
            print(e)

    def get_sequence(self, name):
        document = self.msgcoll.find_one_and_update({"name": name}, {"$inc": {"value": 1}}, return_document=True)
        return document["value"]




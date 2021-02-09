import pymongo


class MongoUtility:
    def __init__(self):
        self.myclient = pymongo.MongoClient(
            "mongodb+srv://root:root@cluster0.iwuxd.mongodb.net/mydatabase?retryWrites=true&w=majority")
        self.mydb = self.myclient["mydatabase"]
        self.mycol = self.mydb["user_data"]

    def check_api_key(self, api_key, database_name, collection_name):
        flag = False
        value = {}
        try:
            for x in self.myclient[database_name] \
                    [collection_name].find({"api_key": api_key}):
                if x:
                    del x["_id"]
                    flag = True
                    value = x
        except Exception as e:
            print(e)
        return value, flag

    def insert_one(self, input_json):
        try:
            mongo_response = self.mycol.insert_one(input_json)
            return mongo_response.inserted_id
        except Exception as e:
            print(e)

from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from tqdm import tqdm

import glob
import json
import os
import sys
import uuid

def connect_to_mongo(mongoUri, mongoDb):
    print(f"Connecting to {mongoDb} at {mongoUri}...")

    try:
        mongoClient = MongoClient(mongoUri, serverSelectionTimeoutMS=5000)
        mongoClient.server_info()  # will throw an exception if can't connect
    
        mongoDb = mongoClient[mongoDb]

        # Verify database exists by attempting an operation
        mongoDb.list_collection_names()
    
        print("Connected successfully...")

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        mongoClient.close()
        sys.exit(1)

    return mongoClient, mongoDb

def get_data_files(dataDir):
    dataFiles = glob.glob(os.path.join(dataDir, "*.js"))
    return dataFiles

def get_or_create_collection(db, collectionName):
    if collectionName not in db.list_collection_names():
        db.create_collection(collectionName)
    return db[collectionName]

def get_item_props(dataName, item):
    dataType = next(iter(item.keys()))
    itemKeys = item[dataType].keys()

    itemIdProp = None
    autogenId = False

    # Priority ordered list of possible ID patterns
    id_patterns = [
        'id',                    # Standard 'id'
        '_id',                   # MongoDB style
        f'{dataName}_id',      # Prefixed with type (e.g., user_id)
        f'{dataName}Id',       # Camel case
        'uuid',                 # UUID
        'guid',                 # GUID
        'identifier'            # Full word
    ]

    # Convert properties to lowercase for case-insensitive matching
    itemKeys_lower = [k.lower() for k in itemKeys]

    # First try exact matches from our priority list
    for pattern in id_patterns:
        if pattern in itemKeys or pattern.lower() in itemKeys_lower:
            itemIdProp = pattern
            break

    # If no exact matches, look for properties containing 'id'
    if itemIdProp is None:
        for prop in itemKeys:
            if 'id' in prop.lower():
                itemIdProp = prop
                exit

    # No ID property found
    if itemIdProp is None:
        itemIdProp = 'guid'
        autogenId = True
        print(f"Warning: No ID property found for {dataName}, using autogen 'guid'")

    return dataType, itemIdProp, autogenId

def generate_guid():
    return str(uuid.uuid4())

def import_data_file(db, dataName, dataFile, skipOnCount = True):
    
    if dataName == "manifest":
        print("Skipping manifest file")
        return

    data = []
    itemCount = 0

    with open(dataFile) as file:
        jsData = file.read()
        jsonData = '[' + jsData.split('[', 1)[1]
        data = json.loads(jsonData)

    fileItemCount = len(data)

    if fileItemCount == 0:
        print(f"No {dataName}(s) found in {dataFile}")
        return

    collection = get_or_create_collection(db, dataName)
    existingItems =  collection.find({})
    existingItemCount = len(list(existingItems))
        
    if fileItemCount == existingItemCount and skipOnCount:
        print(f"Skipping {dataName} import, {fileItemCount} {dataName}(s) already imported")
        return

    print(f"Found {fileItemCount} {dataName}(s) in {dataFile}, {existingItemCount} existing {dataName}(s) in database")

    dataType, itemIdProp, autogenId = get_item_props(dataName, data[0])

    for item in tqdm(data, desc=f"Importing {dataName}(s)", total=fileItemCount):
        itemData = item[dataType]

        if autogenId:
            itemId = itemData[itemIdProp] = generate_guid()
        else:
            itemId = itemData[itemIdProp]
        
        # Check if tweet already exists
        if not collection.count_documents({itemIdProp: itemId}) > 0:
            # print(f"Importing {dataType} #{itemId} ({itemCount})...")
            collection.insert_one(itemData)
            itemCount += 1
        #else:
            # print(f"{dataType} #{itemId} already exists, skipping...")

    print(f"Imported {itemCount} {dataName} from {dataFile}")


# start by getting our config
config = dotenv_values(".env")

mongoUri = config["MONGO_URI"]
mongoDb = config["MONGO_DB"]

# connect to mongo
mongoClient, mongoDatabase = connect_to_mongo(mongoUri, mongoDb)

dataFiles = get_data_files("./data")
for dataFile in dataFiles:
    dataName = os.path.basename(dataFile).split(".")[0]
    import_data_file(mongoDatabase, dataName, dataFile)

mongoClient.close()

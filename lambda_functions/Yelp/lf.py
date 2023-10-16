import requests
import json
import boto3
import datetime
from decimal import Decimal

business_id = "***"

API_KEY =  "***"
ENDPOINT = "https://api.yelp.com/v3/businesses/search"
HEADERS = {'Authorization':"bearer %s" % API_KEY}

PARA = {
    'term':'restaurants',
    'categories':'',
    'limit':1,
    'offset':0,
    'location':'Manhattan'
}

def lambda_handler(event, context):  
    DynamoDB_add_data()
    return


def DynamoDB_add_data():
    db = boto3.resource('dynamodb', region_name='us-east-1')
    table = db.Table("yelp-restaurants")

    with open("DynamoDB.json",'r') as f:
        data = json.load(f)
    
    for i in data:
        i['Rating'] = Decimal(i['Rating'])
        table.put_item(Item=i)
    



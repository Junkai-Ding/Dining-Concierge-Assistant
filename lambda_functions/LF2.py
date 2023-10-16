import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import json
import requests
from requests_aws4auth import AWS4Auth
import random


# Reference: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/search-example.html
# Reference: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html


def receive_sqs():
    url="https://sqs.us-east-1.amazonaws.com/***/Q1"
    response = boto3.client('sqs').receive_message(QueueUrl=url,
                                                   VisibilityTimeout=60,
                                                   MaxNumberOfMessages=1,
                                                   MessageAttributeNames=['All'],
                                                   WaitTimeSeconds=5)
    return response

def delete_sqs(response):
    url = "https://sqs.us-east-1.amazonaws.com/***/Q1"
    handle = response["Messages"][0]['ReceiptHandle']

    boto3.client('sqs').delete_message(QueueUrl=url, ReceiptHandle=handle)

def insert_data(data, db=None, table='last_search'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    response = table.put_item(Item=data)
    print('@insert_data: response', response)
    return response

def update_item(key, featurename, feature, db=None, table='last_search'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)

    response = table.update_item(
        Key=key,
        UpdateExpression="set #feature=:f",
        ExpressionAttributeValues={
            ':f': feature
        },
        ExpressionAttributeNames={
            "#feature": featurename
        },
        ReturnValues="UPDATED_NEW"
    )
    print(response)
    return response

def lookup_data(key, db=None, table='yelp-restaurants'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.get_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
        return {}
    else:
        print(response['Item'])
        return response   

def DynamoDB_query(data):
    
    DynamoDB = boto3.resource("dynamodb")
    table = DynamoDB.Table("yelp-restaurants")

    data_id = 0
    restaurants = []

    for i in data:
        Rid = i["_source"]["RestaurantID"] 
        res = lookup_data({'Business_ID': str(Rid)}) 
        restaurants.append(res["Item"])
        data_id += 1

    ids = random.sample(range(data_id), 3)
    return [restaurants[i] for i in ids]

def send_ses(message, email):
    # create a new SES resource
    client = boto3.client("ses")
    # sender and recipient for testing
    sender = "***@***.***" #email
    charset = "utf-8"
    # try to send the email
    try:
        response = client.send_email(
            Destination={"ToAddresses": [
                email,
            ],
            },
            Message={
                "Body": {
                    "Text": {
                        "Charset": charset,
                        "Data": message,
                    },
                },
                "Subject": {
                    "Charset": charset,
                    "Data": "Restaurant Recommendations",
                },
            },
            Source=sender
        )
        print('success')
    except ClientError as e:
        print(e)


def history_recommend(email, location, cuisine, restaurant, restaurant_address):

    try:
        res = lookup_data({'email': email+"#"+location+"#"+cuisine}, table='last_search')
        restaurant_pre = res["Item"]['Restaurant']
        address_pre = res["Item"]['Address']
        update_item({'email': email+"#"+location+"#"+cuisine},"Restaurant",restaurant)
        update_item({'email': email+"#"+location+"#"+cuisine},"Address",restaurant_address)
        return f"Based on your previous search for {cuisine} restaurant, we recommend {restaurant_pre}, located at {address_pre}, {location}."
        
    except:
        insert_data({
            'email': email+"#"+location+"#"+cuisine,
            'Restaurant': restaurant,
            'Address': restaurant_address
        })
        return ""
        
# Lambda execution starts here
def lambda_handler(event, context):

    msg = receive_sqs()
    
    delete_sqs(msg) #even if we delete sqs, we can still return the msg 
    
    user_request = json.loads(msg['Messages'][0]['Body'])
    
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 
                region, service, session_token=credentials.token)
    
    host = 'https://*****.us-east-1.es.amazonaws.com'
    
    index = 'restaurants'
    url = host + '/' + index + '/_search'
    
    # Put the user query into the query DSL for more accurate search results.
    # Note that certain fields are boosted (^).
    
    cuisine = user_request['Cuisine']['value']['interpretedValue']
    
    query = {
        "size": 10, # number of restaurants queried
        "query": {
            "multi_match": {
                "query": cuisine,
                "fields": ["Cuisine"]
            }
        }
    }

    # Elasticsearch 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }

    # Make the signed HTTP request
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    opensearch_res = json.loads(r.text)   
    res_data = opensearch_res['hits']['hits']
    
    target = DynamoDB_query(res_data)
    
    hist = history_recommend(user_request['Phone_number']['value']['interpretedValue'], user_request['Location']['value']['interpretedValue'], cuisine, target[0]['Name'], target[0]['Address'])
    
    email_content = f"Hello! Here are my {cuisine} restaurant suggestions for {user_request['Number_of_people']['value']['interpretedValue']} people, for {user_request['Date']['value']['interpretedValue']} at {user_request['Dining_time']['value']['interpretedValue']}: 1. {target[0]['Name']}, located at {target[0]['Address']}, 2. {target[1]['Name']}, located at {target[1]['Address']}, 3. {target[2]['Name']}, located at {target[2]['Address']}. Enjoy your meal!"
    
    send_ses(email_content+'\n'+hist,user_request['Phone_number']['value']['interpretedValue'])
    
    
    

    
    
    
    

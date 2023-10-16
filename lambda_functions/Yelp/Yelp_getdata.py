import requests
import json
import boto3
import datetime


business_id = "***"

API_KEY =  "*****"
ENDPOINT = "https://api.yelp.com/v3/businesses/search"
HEADERS = {'Authorization':"bearer %s" % API_KEY}

PARA = {
    'term':'restaurants',
    'categories':'',
    'limit':50,
    'offset':0,
    'location':'Manhattan'
}


def insert_data():
    cuisines = ["american", "chinese", "japanese", "mexican", "korean", "italian", "middle eastern", "french"]

    dynamoDB_data1 = [] # data without repeated restaurant
    business_data = [] # indistinct data
    ids_have = []
    f = open('opensearch.json','w')
    
    count = 0
    for cuisine in cuisines:
        PARA['categories'] = cuisine
        PARA['offset'] = 0
        #for i in range(1): #for test code only
        for i in range(20): #offset has a maximum of 1000
            print(i)
            response = requests.get(url = ENDPOINT, 
                                params = PARA, headers = HEADERS)
            data = response.json().get("businesses")
            data1 = [] # data without repeated restaurant
            for restaurant in data:
                Rid = restaurant['id']
                #print(restaurant)
                if Rid not in ids_have:
                    count += 1
                    data1.append(restaurant)
                    ids_have.append(Rid)
                    ts = datetime.datetime.now().strftime("%m-%d-%Y, %H:%M:%S")
                    #dynamoDB
                    dynamoDB_data1.append({
                            'Business_ID': Rid,
                            'Name': restaurant['name'],
                            'Address':restaurant['location']['address1'],
                            'Coordinates':str(restaurant['coordinates']),
                            'Number_of_Reivews':restaurant['review_count'],
                            'Rating':restaurant['rating'],
                            'Zip_Code':restaurant['location']['zip_code'],
                            'insertedAtTimestamp': ts
                            })
                   
                    json.dump({"index": {"_index": "restaurants", "_id": count}},f)
                    f.write("\n")
                    json.dump({"RestaurantID": Rid , "Cuisine": cuisine },f)
                    f.write("\n")
                    
                else:
                    continue # neglect this restaurant
            business_data.extend(data1)
            #cnt += len(data['businesses'])
            
            PARA['offset'] += PARA['limit'] 
    #print(cnt)
    print(len(business_data)) #total num of restaurant we have
    f.close()
    with open('DynamoDB.json','w') as f:
        json.dump(dynamoDB_data1,f,indent= 4)
        
insert_data()

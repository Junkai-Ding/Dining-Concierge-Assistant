import boto3
import logging
import json, sys
import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#done
def lex_msg(msg_content,msg_type):
    
    return {
        'sessionState': {
            'dialogAction': {
                "type": msg_type #"ElicitIntent"
            }
        },
        'messages': [{
                        'contentType': 'PlainText',
                        'content': msg_content
                    }]
    }

def invalid_msg(sessionAttributes, intent, slots, Wrongslot, msg):
    return {
        'sessionState':{
                'sessionAttributes': sessionAttributes,
                'dialogAction': {
                    'slotToElicit': Wrongslot,
                    'type': 'ElicitSlot'
                },
                'intent': {
                    'name': intent,
                    'slots': slots
                }
        },
        'messages': [{
                        'contentType': 'PlainText',
                        'content': msg
                    }]
    }    

#done
def lambda_handler(event, context):
    print(event)
    intent = event['sessionState']['intent']['name']

    if intent == 'GreetingIntent':
        print("I'm here")
        return lex_msg("Hi there, how can I help?","ElicitIntent")
    elif intent == 'ThankYouIntent':
        return lex_msg("You're welcome.","ElicitIntent") # 
    elif intent == 'DiningSuggestionsIntent':
        return suggestion(event)
    else:
        logger.debug('{} does not match the intent in the system'.format(intent))
        raise Exception(intent + ' is not supported yet.')

#done
def suggestion(event):
    userid = event['sessionId']
    intent = event['sessionState']['intent']['name']
    slots = event['sessionState']['intent']['slots']
    logger.debug('{} suggestion record: intent = {}, slots={}'.format(userid, intent, slots))
    data_type = {}
    count = 0
    for key in slots.keys():
        # Initialization
        if type(slots[key]) != dict:
             slots[key] = {'shape': None, 'value': {'originalValue': None, 'resolvedValues': None, 'interpretedValue': None}}
             data_type[key] = 1
        else: # interpreted value
            if ('interpretedValue' in slots[key]['value'].keys()) and (slots[key]['value']['interpretedValue'] != '') and (slots[key]['value']['interpretedValue'] != None):
                data_type[key] = 0
            else:
                slots[key] = {'shape': None, 'value': {'originalValue': None, 'resolvedValues': None, 'interpretedValue': None}}
                data_type[key] = 0
    Location = slots['Location']['value']['interpretedValue']
    Cuisine = slots['Cuisine']['value']['interpretedValue']
    Date = slots['Date']['value']['interpretedValue']
    Dining_Time = slots['Dining_time']['value']['interpretedValue']
    Num_of_peo = slots['Number_of_people']['value']['interpretedValue']
    Phone_Num = slots['Phone_number']['value']['interpretedValue']
    if event['sessionState']['sessionAttributes'] is not None:
        sessionAttributes = event['sessionState']['sessionAttributes']
    else:
        sessionAttributes = {}
    
        
    if event['invocationSource'] == 'DialogCodeHook':
        logger.debug('Start Dialog Code Hook')
        
        # Invalid Location
        if (data_type['Location'] == 0) and ((Location is None) or (Location.lower() != 'manhattan')):
            Wrongslot = 'Location'
            slots['Location']['value']['interpretedValue'] = None
            msg = 'Sorry! We only support restaurants in Manhattan for search currently.'
            logger.debug('{}, Validation Fail: intent = {}, sessionAttributes = {}, wrong slots = {}, msg = {} '.format(userid,
                intent, sessionAttributes, Wrongslot, msg))
            return invalid_msg(sessionAttributes, intent, slots, Wrongslot, msg)
        elif data_type['Location'] == 0:
            count += 1
        else: pass
    
        # Invalid Cuisine 
        cuisines = ["american", "chinese", "japanese", "mexican", "korean", "italian", "middle eastern", "french"]
        if (data_type['Cuisine'] == 0) and ((Cuisine is None) or (Cuisine.lower() not in cuisines)):
            Wrongslot = 'Cuisine'
            slots['Cuisine']['value']['interpretedValue'] = None
            msg = 'Sorry! Here are cuisines you can choose from: {}.'.format(cuisines)
            logger.debug('{}, Validation Fail: intent = {}, sessionAttributes = {}, wrong slots = {}, msg = {} '.format(userid,
                intent, sessionAttributes, Wrongslot, msg))
            return invalid_msg(sessionAttributes, intent, slots, Wrongslot, msg)     
        elif data_type['Cuisine'] == 0:
            count += 1
        else: pass
        
        # Invalid Date CONTINUE
        if (data_type['Date'] == 0): #slots has dict for key Date
            invalid_date = 0
            if Date is None: #slots['Date']['value']['interpretedValue'] is None
                invalid_date = 1
            else:
                try:
                    proper = (datetime.datetime.strptime(Date, '%Y-%m-%d').date()<datetime.date.today())
                    if proper: invalid_date = 1
                    else: pass
                except: # illegal Date input, not YMD type
                    invalid_date = 1
            if invalid_date == 1:
                Wrongslot = 'Date'
                slots['Date']['value']['interpretedValue'] = None
                msg = 'Sorry! Please enter a valid date.'
                logger.debug('{}, Validation False: intent = {}, sessionAttributes = {}, wrong slots = {}, msg = {} '.format(userid,
                    intent, sessionAttributes, Wrongslot, msg))
                return invalid_msg(sessionAttributes, intent, slots, Wrongslot, msg)
            else: # valid date
                count += 1
        else: pass
        
        # Invalid Dining time
        if data_type['Date'] == 0:
            IsSameDay = (datetime.datetime.strptime(Date, '%Y-%m-%d').date()==datetime.date.today())
        # IsSameDay = 1 : same date, 0 future date
        print(datetime.datetime.now().strftime("%H:%M")) # 
        
        if (data_type['Dining_time'] == 0) and ((Dining_Time is None) or (IsSameDay and Dining_Time<=datetime.datetime.now().strftime("%H:%M"))):
            Wrongslot = 'Dining_time'
            slots['Dining_time']['value']['interpretedValue'] = None
            msg = 'Sorry! Please enter a valid dining time.'
            logger.debug('{}, Validation Fail: intent = {}, sessionAttributes = {}, wrong slots = {}, msg = {} '.format(userid,
                intent, sessionAttributes, Wrongslot, msg))
            return invalid_msg(sessionAttributes, intent, slots, Wrongslot, msg)
        elif data_type['Dining_time'] == 0:
            count += 1
        else: pass
        
        # Invalid Number of people 
        if (data_type['Number_of_people'] == 0) and ((Num_of_peo is None) or ('.' in Num_of_peo) or (int(Num_of_peo) <= 0)):
            Wrongslot = 'Number_of_people'
            slots['Number_of_people']['value']['interpretedValue'] = None
            msg = 'Sorry! Please enter a valid number of people.'
            logger.debug('{}, Validation Fail: intent = {}, sessionAttributes = {}, wrong slots = {}, msg = {} '.format(userid,
                intent, sessionAttributes, Wrongslot, msg))
            return invalid_msg(sessionAttributes, intent, slots, Wrongslot, msg)
        elif data_type['Number_of_people'] == 0:
            count += 1
        else: pass
        
        # Invalid Phone Number    
        if (data_type['Phone_number'] == 0) and (Phone_Num is None) :
            # print("Phone number invalid")
            Wrongslot = 'Phone_number'
            slots['Phone_number']['value']['interpretedValue'] = None
            msg = 'Sorry! Please enter a valid email address.'
            logger.debug('{}, Validation Fail: intent = {}, sessionAttributes = {}, wrong slots = {}, msg = {} '.format(userid,
                intent, sessionAttributes, Wrongslot, msg))
            return invalid_msg(sessionAttributes, intent, slots, Wrongslot, msg)
        elif data_type['Phone_number'] == 0:
            count += 1
        else: pass
        
        logger.debug('{}, Validation Pass: intent = {}, sessionAttributes = {}'.format(userid, intent,
        sessionAttributes))
        
        print("count: {}".format(count))
        if count == len(data_type.keys()):
            msg = "You’re all set. Expect my suggestions shortly! Have a good day."
            #SQS to be continued
            sqs = boto3.client('sqs')
            sqs.send_message(
                QueueUrl="https://sqs.us-east-1.amazonaws.com/******/Q1",
                MessageBody=json.dumps(slots)
            )
            
            logger.debug('Push message to queue..')
            
            print ("I am approaching to close")
            return close(sessionAttributes, intent, 'Fulfilled', msg)
        
        return {
            'sessionState':{
                'sessionAttributes': sessionAttributes,
                'dialogAction': {
                    'type': 'Delegate'
                },
                'intent': {
                    'name': intent,
                    'slots': slots
                }
            }
        }
    


#done
def close(session_attributes, intent, fulfillment_state, msg):
    #close intent
    response = {
        'sessionState':{
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent':{
                'name': intent,
                'state': fulfillment_state
            }
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': msg  
        }]
    }
    #print("I'm here")
    return response

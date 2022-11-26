import json
import boto3
from datetime import datetime
from RoomBooking_Util import checkAvailabilityAtLocation
from RoomBooking_Util import checkAvailabilityOfRoomTypeAtLocation
from RoomBooking_Util import checkStayDurationIsValid
from RoomBooking_Util import IsCheckInDateValid
from RoomBooking_Util import computeCheckOutDate


#Validate all required slots
def validate(slots):
    
    valid_cities = ['Atlanta','New York','Chicago','California','Houston']
    valid_roomTypes = ['Single','Double','Studio','Suite','Presidential Suite']
    
    # Check to see if location slot is given or not
    if not slots['Location']:
        return {
        'isValid': False,
        'violatedSlot': 'Location'
        }        
    
    # check to see if given location is valid one of the valid locations
    if not slots['Location']['value'].get('interpretedValue'):
        return {
        'isValid': False,
        'violatedSlot': 'Location',
        'message' : 'Please click from one of the above buttons for valid Location'
        }
        
    # check to see if given location one of the valid locations
    if slots['Location']['value']['interpretedValue'] not in valid_cities:
        return {
        'isValid': False,
        'violatedSlot': 'Location',
        # 'message': 'We currently  support only {} as a valid destination.?'.format(", ".join(valid_cities))
        'message': 'Please click from one of the above buttons for valid Location'
        }
    
    # Check to see any rooms are avilable or not in the given location 
    location_entered = slots['Location']['value']['interpretedValue']
    is_room_available = checkAvailabilityAtLocation(location_entered)
    if not is_room_available:
        return {
        'isValid': False,
        'violatedSlot': 'Location',
        'message': 'No rooms available in {}. Would you like to try in other location?'.format(location_entered)
        }
    
    # check if CheckInDate is given 
    if not slots['CheckInDate']:
        return {
        'isValid': False,
        'violatedSlot': 'CheckInDate'
    }
    
    # check if given date was being resolved/recognised by lex; If recognised, then user did enyter valid data and not some random string
    if not slots['CheckInDate']['value']['resolvedValues']:
        return {
        'isValid': False,
        'violatedSlot': 'CheckInDate',
        'message': 'Please enter a future valid date.'
        }
    elif not IsCheckInDateValid(slots['CheckInDate']['value']['resolvedValues'][0]):
        return {
            'isValid': False,
            'violatedSlot': 'CheckInDate',
            'message': 'Please enter a future valid date.'
        }
    
    # Check to see if StayDuration slot is given or not
    if not slots['StayDuration']:
        return {
        'isValid': False,
        'violatedSlot': 'StayDuration'
    }
    
    # Check to see if StayDuration slot is given or not
    if not slots['StayDuration']['value'].get('interpretedValue'):
        return {
        'isValid': False,
        'violatedSlot': 'StayDuration',
        'message' : 'Please enter valid stay duration'
    }
    
    # Check to see if StayDuration is greater than 0
    stayDurationIsNotValidMessage = checkStayDurationIsValid(slots['StayDuration']['value']['interpretedValue']) 
    if not stayDurationIsNotValidMessage:
        return {
        'isValid': False,
        'violatedSlot': 'StayDuration',
        'message': 'Please enter valid stay duration. \n Atleast one night of reservation is mandatory. \n For Extended stay more than 10 days, please contact Help Desk: +1469-902-7278.'
    }
    
    
    # Check to see if roomType slot is given or not
    if not slots['RoomType']:
        return {
        'isValid': False,
        'violatedSlot': 'RoomType'
    }
    
    # check to see if given roomtype is one of the valid roomtypes
    if slots['RoomType']['value']['interpretedValue'] not in valid_roomTypes:
        return {
        'isValid': False,
        'violatedSlot': 'RoomType',
        'message': 'We currently support room types: \n {} . \n Please enter above options or click from one of the above buttons for RoomTypes'.format(", ".join(valid_roomTypes))
    }
    
    # Check to see if rooms are available for the give roomType
    roomType_entered = slots['RoomType']['value']['interpretedValue']
    is_roomType_avialble = checkAvailabilityOfRoomTypeAtLocation(location_entered, roomType_entered)
    if not is_roomType_avialble:
        return {
        'isValid': False,
        'violatedSlot': 'RoomType',
        'message': 'No rooms available in {}. Would you like to try other RoomType?'.format(roomType_entered)
    }

    return {'isValid': True}


def handleRoomBooking(event, intent_name):
    
    print("Received EVENT From  handler", event)
    slots = event['sessionState']['intent']['slots']
    
    # Calling validate() to validate all required slots
    validation_result = validate(slots)
    
    if event['invocationSource'] == 'DialogCodeHook':
        
        # if any of the slots are not valid, then run below steps
        if not validation_result['isValid']:
            
            # if non-valid solt validation has a specifc message to send back to customer, then run below steps
            if 'message' in validation_result:
                response={
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit":validation_result['violatedSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            'name':intent_name,
                            'slots': slots
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": validation_result['message']
                        }
                    ]
                }
            # if non-valid solt validation has no specifc message to send back to customer, then run below steps    
            else:
                response = {
                             "sessionState": {
                                    "dialogAction": {
                                        'slotToElicit':validation_result['violatedSlot'],
                                        "type": "ElicitSlot"
                                    },
                                    "intent": {
                                        'name':intent_name,
                                        'slots': slots
                                    }
                                }
                        }
        
        # if all of the slots are valid, then run below steps
        else:
            # Jump to Payment intent
            # preparing session attributes values to pass to payment intent
            Location = slots['Location']['value']['interpretedValue']
            RoomType = slots['RoomType']['value']['interpretedValue']
            CheckInDate = slots['CheckInDate']['value']['interpretedValue']
            StayDuration = slots['StayDuration']['value']['interpretedValue']
            CheckOutDate = computeCheckOutDate(CheckInDate, StayDuration)
            
            response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent": {
                    'name':intent_name,
                    'slots': slots
                },
                "sessionAttributes":{
                    "Location": Location,
                    "CheckInDate" : CheckInDate,
                    "StayDuration" : StayDuration,
                    "RoomType" : RoomType,
                    "CheckOutDate" : CheckOutDate,
                }
            }
        }
        
    # If request is for fullfillment 
    if event['invocationSource'] == 'FulfillmentCodeHook':
        
        response = {
        "sessionState": {
            "dialogAction": {
                "type": "Delegate"
            },
            "intent": {
                'name':intent_name,
                'slots': slots,
                'state':'Fulfilled'
            }
        }
    }
    
    return response
    

    
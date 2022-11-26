import json
import boto3
from UpdateBooking_Util import *
from datetime import datetime


def validate(BookingUpdate_slot):
    """
    Description: The function validates booking ID
    Parameter: BookingUpdate_slot
    returns: Message for the bot based  on the booking.
    """
#validating booking ID    
    print("The BookingUpdate_slot is ",BookingUpdate_slot)
    
    if not BookingUpdate_slot['BookingID']:
        return {
        'isValid': False,
        'violatedSlot': 'BookingID'
        }      
    
    is_valid_booking_id = checkBookingId(BookingUpdate_slot['BookingID']['value']['originalValue'])
    print(is_valid_booking_id)
    if is_valid_booking_id == False:
         return {
            'isValid': False,
            'violatedSlot': 'BookingID',
            'message': 'We cannot find a booking with the provided ID. Kindly provide a valid Booking ID.'
        }

        
    #return {'isValid': True}
    valid_cities = ['Atlanta','New York','Chicago','California','Houston']
    valid_roomTypes = ['Single','Double','Studio','Suite','Presidential Suite']
    
    # Check to see if location slot is given or not
    if not BookingUpdate_slot['Location']:
        return {
        'isValid': False,
        'violatedSlot': 'Location'
        }        
    
    # check to see if given location is valid one of the valid locations
    if not BookingUpdate_slot['Location']['value'].get('interpretedValue'):
        return {
        'isValid': False,
        'violatedSlot': 'Location',
        'message' : 'Please click from one of the above buttons for valid Location'
        }
        
    # check to see if given location one of the valid locations
    if BookingUpdate_slot['Location']['value']['originalValue'] not in valid_cities:
        return {
        'isValid': False,
        'violatedSlot': 'Location',
        #'message': 'We currently  support only {} as a valid destination.?'.format(", ".join(valid_cities))
        #'message': 'Kindly provide the valid Location so that we can help you further.'
        'message': 'Please click from one of the above buttons for valid Location.'
        }
    
    # # Check to see any rooms are avilable or not in the given location 
    location_entered = BookingUpdate_slot['Location']['value']['originalValue']
    is_room_available = checkAvailabilityAtLocation(location_entered)
    if not is_room_available:
        print("Rooms not available in the given location")
        return {
        'isValid': False,
        'violatedSlot': 'Location',
        'message': 'No rooms available in {}. Would you like to try in other location?'.format(location_entered)
        }
    
    # check if CheckInDate is given 
    if not BookingUpdate_slot['StartDate']:
        return {
        'isValid': False,
        'violatedSlot': 'StartDate'
    }
    
    # check if given date is valid and correct.
    if not BookingUpdate_slot['StartDate']['value']['resolvedValues']:
        return {
        'isValid': False,
        'violatedSlot': 'StartDate',
        'message': 'Please enter a future valid date.'
        }
    elif not IsCheckInDateValid(BookingUpdate_slot['StartDate']['value']['resolvedValues'][0]):
        return {
            'isValid': False,
            'violatedSlot': 'StartDate',
            'message': 'Please enter a future valid date.'
        }
    
    
    # Check to see if StayDuration slot is given or not
    if not BookingUpdate_slot['Duration']:
        return {
        'isValid': False,
        'violatedSlot': 'Duration'
    }
    print(BookingUpdate_slot)
     # Check to see if StayDuration slot is given or not
    print("*****",BookingUpdate_slot['Duration']['value']['originalValue'])
    if not BookingUpdate_slot['Duration']['value']['originalValue']:
        return {
        'isValid': False,
        'violatedSlot': 'Duration',
        'message' : 'Please enter valid stay duration'
    }
    
    # Check to see if StayDuration is greater than 0
    stayDurationIsNotValidMessage = checkStayDurationIsValid(BookingUpdate_slot['Duration']['value']['originalValue']) 
    if not stayDurationIsNotValidMessage:
        print("stay duration entered if in validation")
        return {
        'isValid': False,
        'violatedSlot': 'Duration',
        'message': 'Please enter valid stay duration. \n Atleast one night of reservation is mandatory. \n For Extended stay more than 10 days, please contact Help Desk: +1469-902-7278.'
    }
    
    
    # Check to see if roomType slot is given or not
    if not BookingUpdate_slot['RoomType']:
        return {
        'isValid': False,
        'violatedSlot': 'RoomType'
    }
    
    # check to see if given roomtype is one of the valid roomtypes
    if BookingUpdate_slot['RoomType']['value']['interpretedValue'] not in valid_roomTypes:
        return {
        'isValid': False,
        'violatedSlot': 'RoomType',
        'message': 'We currently support room types: \n {} . \n Please enter above options or click from one of the above buttons for RoomTypes'.format(", ".join(valid_roomTypes))
    }
    
    # Check to see if rooms are available for the give roomType
    roomType_entered = BookingUpdate_slot['RoomType']['value']['interpretedValue']
    is_roomType_avialble = checkAvailabilityOfRoomTypeAtLocation(location_entered, roomType_entered)
    if not is_roomType_avialble:
        print("Rooms of requested type is not available in the given location")
        return {
        'isValid': False,
        'violatedSlot': 'RoomType',
        'message': 'No rooms available in {}. Would you like to try other RoomType?'.format(roomType_entered)
    }


    return {'isValid': True}   
    
def handleUpdateBooking(event, intent_name):
    """
    Description: This function handles booking update
    Parameter: event, intent_name
    returns: Response for the bot based  on the booking.
    """
    print("Received INTENT From handler", intent_name)
    print("Received EVENT From  handler", event)
    BookingUpdate_slot = event['sessionState']['intent']['slots']
    print("Received:::: ", BookingUpdate_slot)
    
     # Calling validate() to validate all required slots
    validation_result = validate(BookingUpdate_slot)
    
    if event['invocationSource'] == 'DialogCodeHook':
        
        if not validation_result['isValid']:
            # wrong user inputs, ask again
            if 'message' in validation_result:
                # build a new response with message.
                response = {
                             "sessionState": {
                                "dialogAction": {
                                    'slotToElicit':validation_result['violatedSlot'],
                                    "type": "ElicitSlot"
                                    
                                    
                                },
                                "intent": {
                                        'name':intent_name,
                                        'slots': BookingUpdate_slot
                                        
                                    
                                }
                                    
                                 
                            },
                            "messages": [
                                {
                                  "contentType": "PlainText",
                                  "content": validation_result['message']
                                }
                            ]
                        }
            else:
                response = {
                             "sessionState": {
                                    "dialogAction": {
                                        'slotToElicit':validation_result['violatedSlot'],
                                        "type": "ElicitSlot"
                                    },
                                    "intent": {
                                        'name':intent_name,
                                        'slots': BookingUpdate_slot
                                        
                                    }
                                }
                        }    
            
        else:
            # correct user inputs

            RoomType = BookingUpdate_slot['RoomType']['value']['originalValue']
            Duration = BookingUpdate_slot['Duration']['value']['originalValue']
            StartDate = BookingUpdate_slot['StartDate']['value']['resolvedValues'][0]
            print(type(StartDate))
            CheckOutDate = computeCheckOutDate(StartDate, Duration)
            
            # Compute final billing amount and send to customer to ask for confirmation
            TotalBillingAmount = computeTotalAmount(RoomType, Duration)
            
            response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent": {
                    'name':intent_name,
                    'slots': BookingUpdate_slot
                    
                },
                "sessionAttributes":{
                    "session_attributes": TotalBillingAmount,
                    "session_attributes1": CheckOutDate,
                    
                    }
                
            }
            }
    
    confirmation = event['sessionState']['intent']['confirmationState']
    # Update booking status for the bookingID.
    if confirmation == "Confirmed":
        print("Inside update ConfirmIntent flow")
        # Generate Booking Id for the customer
        bookingID = BookingUpdate_slot['BookingID']['value']['originalValue']
        
        # Update booking status in BookingDetailsTable
        update_response = updateTableRecords(BookingUpdate_slot)
        print("Update Response", update_response)

    if event['invocationSource'] == 'FulfillmentCodeHook':

        # Add order in Database

        response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                'name':intent_name,
                'slots': BookingUpdate_slot,
                'state':'Fulfilled'

                }

        }
        
    }
    print("RESPONSE AT END",response)
    return response 



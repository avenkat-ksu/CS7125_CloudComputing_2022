import boto3
from Payment_Util import ValidateCreditCardNumber
from Payment_Util import validateCreditCardDate
from Payment_Util import ValidateCardSecurityCode
from Payment_Util import computeTotalAmount
from Payment_Util import storeBookingDetailsToDB

#Validate all required slots
def validate(slots, session_attributes):
    
    # Check to see if CreditCardNumber slot is given or not
    if not slots['CreditCardNumber']:
        return {
        'isValid': False,
        'violatedSlot': 'CreditCardNumber'
        }        
    
    # check to see if given CreditCardNumber is valid
    EnteredCreditCardNumber = slots['CreditCardNumber']['value']['originalValue']
    isCardValid = ValidateCreditCardNumber(EnteredCreditCardNumber)
    if not isCardValid:
        return {
        'isValid': False,
        'violatedSlot': 'CreditCardNumber',
        'message': 'Please enter a valid credit card number of 15 or 16 digit as per your card provider'
        }
    
    # check if CardSecurityCode is given 
    if not slots['CardSecurityCode']:
        return {
        'isValid': False,
        'violatedSlot': 'CardSecurityCode',
    }
    
    # Check to see CardSecurityCode is valid or not 
    EnteredCardSecurityCode = slots['CardSecurityCode']['value']['originalValue']
    isSecurityCodeValid = ValidateCardSecurityCode(EnteredCardSecurityCode)
    if not isSecurityCodeValid:
        print("Given security code is not valid")
        return {
        'isValid': False,
        'violatedSlot': 'Location',
        'message': 'Please Enter a valid security code of 3 or 4 digits as per your card provider'
        }
        
    # Check to see if CardExpiryDate slot is given or not
    if not slots['CardExpiryDate']:
        return {
        'isValid': False,
        'violatedSlot': 'CardExpiryDate'
    }
    
    # check if given CardExpiryDate was being resolved/recognised by lex; If recognised, then user did enyter valid data and not some random string
    print("slots['CardExpiryDate']['value']['originalValue']", slots['CardExpiryDate']['value']['originalValue'])
    if not validateCreditCardDate(session_attributes['CheckInDate'], slots['CardExpiryDate']['value']['originalValue']):
        return {
        'isValid': False,
        'violatedSlot': 'CardExpiryDate',
        'message': 'Please enter a valid card expiry date in MM/YY format.'
        }

    # Check to see if nameOnCard slot is given or not
    if not slots['NameOnTheCard']:
        return {
        'isValid': False,
        'violatedSlot': 'NameOnTheCard'
    }
    
    return {'isValid': True}


def handlePayment(event, intent_name):
    
    print("Received EVENT From  handler", event)
    slots = event['sessionState']['intent']['slots']
    session_attributes = event['sessionState']['sessionAttributes']
    
    # Calling validate() to validate all required slots
    validation_result = validate(slots, session_attributes)
    
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
                print("slot validation failed and has NO message")
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
            # Fetch session attritube values here
            RoomType = session_attributes['RoomType']
            StayDuration = session_attributes['StayDuration']
            
            # Compute final billing amount and send to customer to ask for confirmation
            TotalBillingAmount = computeTotalAmount(RoomType, StayDuration)
            
            # Add TotalBillingAmount to session attributes to dispaly it to customer
            session_attributes ["TotalBillingAmount"] = TotalBillingAmount
            
            # Send message to get customer confirmation
            response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent": {
                    'name':intent_name,
                    'slots': slots
                },
                "sessionAttributes":session_attributes
            }
        }
    
    # If customer confirms for previous requst and current request is for fullfillment 
    if event['invocationSource'] == 'FulfillmentCodeHook':
        
        # generate bookingId and store BookingDetails along with payment details To DB
        bookingId = storeBookingDetailsToDB(event['sessionState']['sessionAttributes'], slots)
        
        # Return BookingId back to customer along with confirmation of booking.
        session_attributes ["BookingID"] = bookingId
        response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent": {
                    'name':intent_name,
                    'slots': slots
                },
                "sessionAttributes":session_attributes
            }
        }

    return response
    
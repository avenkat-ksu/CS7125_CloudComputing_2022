
from CancelBooking_Util import checkBookingId, updateCancellationRecords, checkCancellationPolicy

#Validate all required slots
def validate(cancellation_slots):
    
    if not cancellation_slots['CancelBookingID']:
        return {
        'isValid': False,
        'violatedSlot': 'CancelBookingID'
        }      
    
    is_valid_booking_id = checkBookingId(cancellation_slots['CancelBookingID']['value']['originalValue'])
    print(is_valid_booking_id)
    if is_valid_booking_id == False:
         return {
        'isValid': False,
        'violatedSlot': 'CancelBookingID',
        'message': 'We cannot find a booking with the given ID. Please give a valid Booking ID.'
        }
    
    return {'isValid': True}
    
    
def handleCancelBooking(event, intent_name):
    
    print("Received INTENT From handler", intent_name)
    print("Received EVENT From  handler", event)
    cancellation_slots = event['sessionState']['intent']['slots']
    
    # Calling validate() to validate all required slots
    validation_result = validate(cancellation_slots)
    print("VALIDATION RESULT inside handleCancelBooking", validation_result)
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
                                        'slots': cancellation_slots
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
                                        'slots': cancellation_slots
                                        }
                                    }
                        }            
            
            
        else:
            # correct user inputs
            print("ALL USER INPUTS ARE CORRECT")
            
            charge_cancel_fee = checkCancellationPolicy(cancellation_slots['CancelBookingID']['value']['originalValue'])
            # cancellation_charges_message = ""
            cancel_booking_id = cancellation_slots['CancelBookingID']['value']['originalValue']
            if charge_cancel_fee:
                cancellation_charges_message = "Please note that $50 cancellation charges will be applied as you are cancelling within 72 hours of the check-in time. "
            else:
                cancellation_charges_message = ""
            
            response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent": {
                    'name':intent_name,
                    'slots': cancellation_slots
                },
                 "sessionAttributes":{
                    "CancelBookingID_Sess_Attr": cancel_booking_id,
                    "Cancellation_Charges_Message": cancellation_charges_message
                }
        
            }
            }
        
    # If request is for fullfillment 
    if event['invocationSource'] == 'FulfillmentCodeHook':
        print("Inside Cancel Fulfillment")

        # Add order in Database
        # Generate Booking Id for the customer
        bookingID = cancellation_slots['CancelBookingID']['value']['originalValue']
        
        # Update booking status in BookingDetailsTable
        cancellation_response = updateCancellationRecords(bookingID)
        print("Cancellation Response", cancellation_response)

        response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                'name':intent_name,
                'slots': cancellation_slots,
                'state':'Fulfilled'
                }

        }
    }
    print("RESPONSE AT END OF CANCEL FLOW",response)
    return response
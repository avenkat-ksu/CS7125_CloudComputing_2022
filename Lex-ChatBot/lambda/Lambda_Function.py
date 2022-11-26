from RoomBookingFlow import handleRoomBooking
from CancelBookingFlow import handleCancelBooking

from PaymentFlow import handlePayment
from UpdateBookingFlow import handleUpdateBooking

def lambda_handler(event, context):
    
    print("Received EVENT in handler", event)

    intent_name = event['sessionState']['intent']['name']
    
    if intent_name == "RoomBooking":
        response = handleRoomBooking(event, intent_name)
    elif intent_name == "RoomCancellation":
        response = handleCancelBooking(event, intent_name)
    elif intent_name == "PaymentIntent":
        response = handlePayment(event, intent_name)
    elif intent_name == "BookingUpdate":
        response = handleUpdateBooking(event, intent_name)
    #intent doesnt match any valid intetn in this bot
    else:
        print("intent doesnt match any valid intetn in this bot")
        
    return response
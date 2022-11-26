import boto3
import json
from datetime import datetime

ROOMS_MAPPING = {"Single":"AvailableSingleRooms",
"Double":"AvailableDoubleRooms" , 
"Studio":"AvailableStudioRooms",
"Suite":"AvailableSuiteRooms",
"Presidential Suite":"AvailablePresidentialSuiteRooms"}

client = boto3.client("dynamodb")

#check if booking ID is valid
def checkBookingId(booking_id):
    print("Inside checkBookingId() ")
    response = client.get_item(
        TableName="BookingDetailsTable",
        Key={
            "BookingID":{
            'S': booking_id
            }
        }
        )
        
    print(f'Response from DB for {booking_id} : {response}')
    
    if 'Item' in response.keys():
        booking_status = response["Item"]["BookingStatus"]["S"]
        if booking_status == "inactive":
            return False
        return True
    return False

#check if cancellation charges apply
def checkCancellationPolicy(booking_id):
    response = client.get_item(
        TableName="BookingDetailsTable",
        Key={
            "BookingID":{
            'S': booking_id
            }
        }
        )
    
    check_in_date = response["Item"]["CheckInDate"]["S"]
    check_in_date = datetime.strptime(check_in_date, "%Y-%m-%d")

    TodaysDate = datetime.now()
    days_left_to_checkin = check_in_date - TodaysDate
    days_left_to_checkin = int(days_left_to_checkin.days)
    print("days_left_to_checkin", days_left_to_checkin)
    
    if days_left_to_checkin <= 3:
        print("Apply 50 usd as cancellation fees")
        return True
    return False

#update booking status in DB 
def updateCancellationRecords(booking_id):
    booking_details_response = client.update_item(
                                TableName="BookingDetailsTable",
                                Key={"BookingID":{"S": booking_id}},
                                UpdateExpression="set BookingStatus = :updated_status",
                                ExpressionAttributeValues = {":updated_status": {"S":"inactive"}},
                                ReturnValues="UPDATED_NEW"
                                )
                                
    room_details_response = updateRoomAvailability(booking_id)
    return booking_details_response

#update room availability in DB
def updateRoomAvailability(booking_id):
    get_response = client.get_item(
        TableName="BookingDetailsTable",
        Key={
            "BookingID":{
            'S': booking_id
            }
        }
        )
        
    print(f'RESPONSE {get_response}')
    item = get_response["Item"]
    location = item['BookingLocation']['S']
    room_type = item['RoomType']['S']
    roomTypeAttribute = ROOMS_MAPPING.get(room_type)
    print("CHECKING", location, room_type,roomTypeAttribute)
    
    # Now increment both totalAvailableRooms and SpecificAvailableRooms value by 1 
    
    response = client.update_item(
        TableName="HotelDetailsTable",
        Key={'HotelLocation': {
            'S': location
            }
        },
        UpdateExpression="SET "+roomTypeAttribute+"= "+roomTypeAttribute+" + :val, TotalAvailableRooms = TotalAvailableRooms + :val",
        ExpressionAttributeValues={":val":{"N":"1"}},
        ReturnValues="UPDATED_NEW"
        )
        
    print("After incrementing AvailableRooms of specific roomType : "+ str(response['Attributes'][roomTypeAttribute]['N']))
    print("After incrementing TotalAvailableRooms: "+ str(response['Attributes']['TotalAvailableRooms']['N']))
    return response
    
    
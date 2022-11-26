import boto3
import json
from datetime import datetime
from datetime import timedelta

BOOKING_DETAILS_DB = "BookingDetailsTable"
HOTEL_DETAILS_DB = "HotelDetailsTable"

RANDOM_ID_LENGTH = 5
ROOMS_MAPPING = {"Single":"AvailableSingleRooms",
"Double":"AvailableDoubleRooms" , 
"Studio":"AvailableStudioRooms",
"Suite":"AvailableSuiteRooms",
"Presidential Suite":"AvailablePresidentialSuiteRooms"}

client = boto3.client("dynamodb")

def checkBookingId(booking_id):
    """
    Description: The function checks if booking ID is valid
    Parameter: booking_id
    returns: True or False
    """
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

   
def getRoomtypeAttributeValue(roomType):
    """
    Description: The function fetches the right Roomtype Attribute in DB for given roomType
    Parameter: roomType
    returns: Type of room
    """

    roomType = roomType.lower()
    
    if roomType == "single":
        roomAttribute = "AvailableSingleRooms"
    elif roomType == "double":
        roomAttribute = "AvailableDoubleRooms"
    elif roomType == "studio":
        roomAttribute = "AvailableStudioRooms"
    elif roomType == "suite":
        roomAttribute = "AvailableSuiteRooms"
    elif roomType == "presidential suite":
        roomAttribute = "AvailablePresidentialSuiteRooms"
    else:
        return False
        
    return roomAttribute




def checkAvailabilityAtLocation(location):
    """
    Description: The function checks if rooms are available in the given location
    Parameter: location
    returns: True or False
    """

    print("Inside checkAvailabilityAtLocation() ")
    print("Location is " + str(location))
    response = client.get_item(
        TableName="HotelDetailsTable",
        Key={
            'HotelLocation': {
            'S': location
            }
        }
        )

    print(f'RESPONSE {response}')
  
    if 'Item' in response.keys():
        availability = response['Item']['TotalAvailableRooms']["N"]
        print("Given "+ location + " has " + str(availability) + " total availability")
        if int(availability) > 0:
            return True
        else:
            return False


def IsCheckInDateValid(checkInDate):
    """
    Description: The function checks if given date is past date
    Parameter: checkinDate
    returns: True or False
    """

    print("Inside IsCheckInDateValid() with date: ", checkInDate)
    TodaysDate = datetime.now()
    StartDate = datetime.strptime(str(checkInDate), "%Y-%m-%d")
    print(StartDate)
    print("Todays date ", TodaysDate)
    if TodaysDate >= StartDate:
        if StartDate >timedelta(days=185):
            print("No valid")
            return False
    else:
        print("Valid")
        return True
    
    
def checkStayDurationIsValid(stayDuration):
    """
    Description: The function checks if StayDuration is Valid ie is atleast one day
    Parameter: stayDuration
    returns: True or False
    """

    print("Inside checkStayDurationISValid() ")
    print("stayDuration is " + str(stayDuration))
    
    if stayDuration.isdigit():
        stayDuration = int(stayDuration)
    else:
        return False
  
    if (int(stayDuration) > 0) and (int(stayDuration) <= 10):
        return True
    else:
        return False  
        
        
def checkAvailabilityOfRoomTypeAtLocation(location, roomType):
    """
    Description: The function checks if rooms are available for the given roomType at the given location
    Parameter: location and roomType
    returns: True or False
    """

    print("Inside checkAvailabilityOfRoomTypeAtLocation() ")
    print("Given Location is " + str(location))
    print("Given RoomType is " + str(roomType))
    response = client.get_item(
        TableName="HotelDetailsTable",
        Key={
            'HotelLocation': {
            'S': location
            }
        }
        )
    
    roomTypeAttribute = ROOMS_MAPPING.get(roomType)
    print(response)
    print(f'RESPONSE {response}')
    #item = response["Item"]
    
    if 'Item' in response.keys():
        availability =  response['Item'][roomTypeAttribute]["N"]
        print("Given "+ roomType + " Type, has " + str(availability) + " availability")
        if int(availability) > 0:
            return True
        else:
            return False
    

   
def computeCheckOutDate(StartDate, Duration):
    """
    Description: The function computes CheckOutDate starting from CheckInDate using StayDuration count
    Parameter: StartDate, Duration
    returns: Calculated End date of the stay
    """
    TodaysDate = datetime.now()
    # conversion between string to datetime object
    Begindate = datetime.strptime(StartDate, "%Y-%m-%d")
  
    # calculating end date by adding StayDuration days
    Enddate = Begindate + timedelta(days=int(Duration))
  
    print("Calculated CheckOutDate: "+ str(Enddate))
    Enddate = datetime.strftime(Enddate, "%Y-%m-%d")
    return Enddate

    
def updateTableRecords(BookingUpdate_slot):
    """
    Description: The function updates the database(DynamoDB) with the new details provided by customer
    Parameter: BookingUpdate_slot
    returns: Room details to be updated
    """
    booking_id = BookingUpdate_slot['BookingID']['value']['originalValue']
    location = BookingUpdate_slot['Location']['value']['originalValue']
    roomType = BookingUpdate_slot['RoomType']['value']['originalValue']
    duration = BookingUpdate_slot['Duration']['value']['originalValue']
    pricechange = computeTotalAmount(roomType, duration)
    print(BookingUpdate_slot['StartDate']['value'])
    print(type(BookingUpdate_slot['StartDate']['value']['originalValue']))
    SD = BookingUpdate_slot['StartDate']['value']['resolvedValues'][0]
    checkout = computeCheckOutDate(SD, duration)
    booking_details_response = client.update_item(
                                TableName="BookingDetailsTable",
                                Key={"BookingID":{"S": booking_id}},
                                UpdateExpression="set BookingLocation= :location, RoomType= :roomType, CheckInDate= :SD, CheckOutDate= :checkout, StayDuration= :duration, AmountDueAtCheckIn= :pricechange",
                                ExpressionAttributeValues = {":location": {"S": location}, ":roomType": {"S": roomType}, ":SD": {"S": SD}, ":checkout": {"S": checkout}, ":duration": {"N": duration}, ":pricechange": {"S": str(pricechange)}},
                                ReturnValues="UPDATED_NEW"
                                )
    
                                
    room_details_free = updateRoomAvailability(booking_id)
    room_details_updates = UpdateAvailableRoomsCount(location, roomType)
    return room_details_updates


def updateRoomAvailability(booking_id):
    """
    Description: The function updates the room count(increment) to release the previously booked roomtype
    Parameter: booking_id
    returns: None
    """
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
    
 #update the Room count as per the new request
def UpdateAvailableRoomsCount(location, roomType):
    """
    Description: The function updates the room count(decrement) to release the previously booked roomtype
    Parameter: location, roomType
    returns: None
    """

    roomTypeAttribute = getRoomtypeAttributeValue(roomType)
        
    print("Attribute of given roomType : "+ str(roomTypeAttribute))
    
    # Now decrese both totalAvailableRooms and SpecificAvailableRooms value by 1 for the updated value
    data = client.update_item(
        TableName="HotelDetailsTable",
        Key={'HotelLocation': {
            'S': location
            }
        },
        UpdateExpression="SET "+roomTypeAttribute+"= "+roomTypeAttribute+" - :decr, TotalAvailableRooms = TotalAvailableRooms - :decr",
        ExpressionAttributeValues={":decr":{"N":"1"}},
        ReturnValues="UPDATED_NEW"
        )
        
    print("After decrementing AvailableRooms of specific roomType : "+ str(data['Attributes'][roomTypeAttribute]['N']))
    print("After decrementing TotalAvailableRooms: "+ str(data['Attributes']['TotalAvailableRooms']['N']))

def computeTotalAmount(RoomType, Duration):
    """
    Description: The function computes revised amount
    Parameter: RoomType, Duration
    returns: totalPriceForBooking
    """

    print("Inside computeTotalAmount() ")
    print("RoomType is ",RoomType)
    print("StayDuration is " ,Duration)
    response = client.get_item(
        TableName='RoomPriceDetailsTable',
        Key={
            'RoomType': {
            'S': RoomType
            }
        }
        )
    pricePerRoom = response['Item']['PricePerRoom']['N']
    print("Given "+ RoomType + " has " + str(pricePerRoom) + " price per room")
    totalPriceForBooking = int(pricePerRoom) * int(Duration)
    
    return totalPriceForBooking    
     
import string
import secrets
import boto3
import json
from datetime import datetime
from datetime import timedelta


RANDOM_ID_LENGTH = 5
ROOMS_MAPPING = {"Single":"AvailableSingleRooms",
"Double":"AvailableDoubleRooms" , 
"Studio":"AvailableStudioRooms",
"Suite":"AvailableSuiteRooms",
"Presidential Suite":"AvailablePresidentialSuiteRooms"}

client = boto3.client('dynamodb')

# Checks if rooms are available in the given location
def checkAvailabilityAtLocation(location):
    print("Inside checkAvailabilityAtLocation() with Location: ", location)
    response = client.get_item(
        TableName='HotelDetailsTable',
        Key={
            'HotelLocation': {
            'S': location
            }
        }
        )
    availability = response['Item']['TotalAvailableRooms']["N"]
    print("Given "+ location + " has " + str(availability) + " total availability")
    if int(availability) > 0:
        return True
    else:
        return False
        
# Check if given date is past date
def IsCheckInDateValid(checkInDate):
    print("Inside IsCheckInDateValid() with date: ", checkInDate)
    TodaysDate = datetime.now().date()
    CheckInDate = datetime.strptime(str(checkInDate), "%Y-%m-%d").date()
    
    # If checkInDate is past date i.e lesser than today's date
    if CheckInDate < TodaysDate:
        return False
    else:
        return True
    
    
# check if StayDuration is Valid ie is atleast one day
def checkStayDurationIsValid(stayDuration):
    print("Inside checkStayDurationISValid() with StayDuration: ",stayDuration)
    
    if stayDuration.isdigit():
        stayDuration = int(stayDuration)
    else:
        return False
  
    if (int(stayDuration) > 0) and (int(stayDuration) <= 10):
        return True
    else:
        return False

    
# Checks if rooms are available for the given roomType at the given location
def checkAvailabilityOfRoomTypeAtLocation(location, roomType):
    print("Inside checkAvialabilityOfRoomTypeAtLocation() with Location: "+ str(location) +" and RoomType: "+ str(roomType))
    
    response = client.get_item(
        TableName="HotelDetailsTable",
        Key={
            'HotelLocation': {
            'S': location
            }
        }
        )
    
    roomTypeAttribute = ROOMS_MAPPING.get(roomType)
    
    availability =  response['Item'][roomTypeAttribute]["N"]
    print("Given "+ roomType + " Type, has " + str(availability) + " availability")
    if int(availability) > 0:
        return True
    else:
        return False
    

# Compute CheckOutDate starting from CheckInDate using StayDuration count   
def computeCheckOutDate(CheckInDate, StayDuration):
    print("Inside computeCheckOutDate() with CheckInDate: "+ str(CheckInDate)+" and Duration: "+ str(StayDuration))
    
    # conversion between string to datetime object
    Begindate = datetime.strptime(CheckInDate, "%Y-%m-%d")
  
    # calculating end date by adding StayDuration days
    Enddate = Begindate + timedelta(days=int(StayDuration))
  
    print("Calculated CheckOutDate: "+ str(Enddate))
    Enddate = datetime.strftime(Enddate, "%Y-%m-%d")
    return Enddate
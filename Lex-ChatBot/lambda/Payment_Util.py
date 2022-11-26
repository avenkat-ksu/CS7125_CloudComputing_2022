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

# credit CreditCardNumber validation
def ValidateCreditCardNumber(creditCardNumber):
    print("Inside ValidateCreditCardNumber() with CreditCardNumber: "+creditCardNumber)
    
    # if CreditCardNumber given is valid and of length 15 or 16
    if (creditCardNumber.isdigit()) and (len(str(creditCardNumber)) == 16 or len(str(creditCardNumber)) == 15 ):
        return True
    else:
        return False


# credit Card date validation
def validateCreditCardDate(CheckInDate, creditCardDate):
    print("Inside validateCreditCardDate() with creditCardDate: "+creditCardDate+ "CheckInDate: "+CheckInDate)
    
    CheckInDate = datetime.strptime(CheckInDate, "%Y-%m-%d")
    try:
        creditCardDate = datetime.strptime(creditCardDate, '%m/%y')
    except ValueError:
        return False
    
    # check if creditCard ExpiryDate is earlier tahan CheckInDate 
    if CheckInDate >= creditCardDate:
        return False
    else:
        return True
        

# credit card security code Validation
def ValidateCardSecurityCode(securityCode):
    print("Inside ValidateCardSecurityCode() with securityCode: "+securityCode)
    
    # Check if given security code is valid and of lenght 3 or 4
    if (securityCode.isdigit()) and (len(str(securityCode)) == 3 or len(str(securityCode)) == 3 ):
        return True
    else:
        return False
    

# Compute Total billing amount: CostPerNightForRoom * NoOfNights
def computeTotalAmount(RoomType, StayDuration):
    print("Inside computeTotalAmount() with RoomType: "+ RoomType+ " StayDuration: "+ StayDuration)

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
    totalPriceForBooking = int(pricePerRoom) * int(StayDuration)
    return totalPriceForBooking
    

# Generate Random alphanumber string for BookingID
def generateBookingId():
    print("Inside generateBookingId() ")
    generatedBookingId = ''.join(
        secrets.choice(string.ascii_letters + string.digits)
        for _ in range(RANDOM_ID_LENGTH)
    )
    return generatedBookingId
    
    
# store booking details to HotelReservationTable
def storeBookingDetailsToDB(sessionAttributes, slots):
    print("Inside storeBookingDetailsToDB() ")
    BookingLocation = sessionAttributes['Location']
    CheckInDate = sessionAttributes['CheckInDate']
    CheckOutDate = sessionAttributes['CheckOutDate']
    RoomType = sessionAttributes['RoomType']
    StayDuration = sessionAttributes['StayDuration']
    
    NameOnTheCard = slots['NameOnTheCard']['value']['originalValue']
    CreditCardNumber = slots['CreditCardNumber']['value']['originalValue']
    CardSecurityCode = slots['CardSecurityCode']['value']['originalValue']
    CardExpiryDate = slots['CardExpiryDate']['value']['originalValue']
    AmountDueAtCheckIn = sessionAttributes['TotalBillingAmount']
    
    # Call generateBookingId()
    bookingId = generateBookingId()
    
    data = client.put_item(
        TableName='BookingDetailsTable',
        Item={
            'BookingID': {
            'S': bookingId
            },
            'BookingLocation': {
            'S': BookingLocation
            },
            'CheckInDate': {
            'S': CheckInDate
            },
            'CheckOutDate': {
            'S': CheckOutDate
            },
            'StayDuration': {
            'N': StayDuration
            },
            'RoomType': {
            'S': RoomType
            },
            'BookingStatus': {
            'S': "active"
            },
            'NameOnTheCard': {
            'S': NameOnTheCard
            },
            'CreditCardNumber': {
            'N': CreditCardNumber
            },
            'CardSecurityCode': {
            'N': CardSecurityCode
            },
            'CardExpiryDate': {
            'S': CardExpiryDate
            },
            'AmountDueAtCheckIn': {
            'N': AmountDueAtCheckIn
            }
        }
        )
    
    # Calling method to update available rooms counter
    UpdateAvailableRoomsCount(BookingLocation, RoomType)
    
    return bookingId
    
    
    
# Method to Reduce the counter of TotalAvailableRooms and SpecificRoomType for given location    
def UpdateAvailableRoomsCount(location, roomType):
    
    roomTypeAttribute = ROOMS_MAPPING.get(roomType)
    
    # Now decrese both totalAvailableRooms and SpecificAvailableRooms value by 1 
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
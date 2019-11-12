import requests
# This action notifies the user when a VM is ready (with it's IP address), via text message.
# It does this by looking for the "To" tag, and expects the value to be a single cell phone number.
# I've tested this with country codes and without.
# The texting service I used is Twilio (twilio.com). 

# There are three local inputs tied to this action:
## "from" - which you can use a number Twilio gives you (which opens up a "chat bot" capability)
## "auth" - the expected value is "Basic <base64 of [token:secret]>"
## "tAccount" - is your Twilio account number

def handler(context, inputs):
    # Grab local inputs
    from_number = inputs['from']
    basicAuth = inputs["auth"]
    tAccount = inputs["tAccount"]
    
    # Grab passed-through inputs
    to_number = inputs['tags']["To"]
    ipAddr = inputs["addresses"][0]
    
    # Build url
    url = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json".format(tAccount)
    
    # to_number can either have a leading country code or not (tested with US numbers)
    # Body is what the text message will say.
    payload = {
        "To":to_number, 
        "From":from_number, 
        "Body":"Your VM is ready! IP address is " + str(ipAddr)
    }
    print("payload...")
    print(payload)
    head = {
        'Accept':'application/json',
        'Content-Type':'application/x-www-form-urlencoded',
        'Authorization':basicAuth
    }
    print("header...")
    print(head)
    
    # perform HTTP POST request
    print("attempting the post...")
    r = requests.post(url, data=payload, headers=head)
    print("result...")
    print(r)

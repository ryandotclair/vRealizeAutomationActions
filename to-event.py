'''
This action sends creates an event in Tanzu Observability. 

Input Requirements:
- "token". This is your Tanzu Observability API token in it ( ex: xxxxxx-yyyy-zzzz-aaaa-bbbbbbbbbbbb )
- "uri". This is your base URL ( ex: surf.wavefront.com )

Subscription Recommendations:
I recommend keying on "Deployment Completed" event. And I would add this to the filter: 
  event.data.eventType == 'CREATE_DEPLOYMENT'

By default it will key on both creation and deletion events if you don't.
'''



import requests
import time

def handler(context, inputs):

    print("Grabbing timestamp...")
    # Time stamp to capture the mandatory window of the event
    start = time.time()
    time.sleep(1)
    end = time.time()
    
    # Build the API call
    h = {"Accept":"application/json","Content-Type":"application/json", "Authorization":"Bearer " + inputs["token"] }
    
    payload = {
        "name": "vRA Deployment Creation Event",
        "annotations": {
            "severity": "info",
            "type": "vRA Deployment",
            "details": "vRA Deployment Created. ID: " + inputs["deploymentId"]
        },
        "tags" : [
            "vRA Deployment"
        ],
        "startTime": start,
        "endTime": end   
    }
    print("Sending wavefront API call...")
    r = requests.post("https://" + inputs["uri"] + "/api/v2/event",headers=h,json=payload,verify=False).json()
    print("Return value is...")
    print(r)

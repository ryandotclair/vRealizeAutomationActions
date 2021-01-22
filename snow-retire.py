
'''
This is the ServiceNow Retire Workflow Action
It updates the existing CMDB record, createts a Change Request, and then Closes the Change Record once done
Tested on vRA 8.0 and vRA Cloud. Tested on SNOW's London release

Assumptions:
- A vRA deployment is the trackable unit, and is recorded in the CMDB, regardless of how many 
    VM's are deployed. 
- Only the first IP address that's reported is recorded (if there's multi-nic VMs)
- CMDB table name (u_cmdb_ci_cloud_instance) and many custom field names (lines 95-102)
- 'requests' is imported, and proper local environments are set (see lines 23-26)
- The event that's being subscribed to is "Compute post removal" 

Special thanks to Pete Picnic for adding the code that retires ALL VMs in the deployment.

'''

import requests

def handler(context, inputs):
    ## Import local environment variables
    snowURI = inputs["snowURI"] # Service Now URL (Ex: https://devxxx.service-now.com/api/now/table/)
    snowCred = inputs["snowCred"] # Service Now auth header. (Ex: Basic <base64 of user:pass>)
    vraToken = inputs["token"] # this is your API token within vRA. We use it later to generate the bearer token
    vraURI = inputs["vraURI"] # This is the vRA URL (ex: https://api.mgmt.cloud.vmware.com/ )
    
    print("Here are the inputs from the Deployment...")
    print("inputs")
    
    ## Capture config data from deployment
    deploymentID = inputs["deploymentId"]
    requesterName = inputs["__metadata"]["userName"]
    # ipAddr = inputs["addresses"][0] #grabs first IP address
    timeStamp = inputs["__metadata"]["timeStamp"]

    # Grab bearer token
    bearer_token = get_vRA_Cloud_bearer_token(inputs["token"])
    
    ## Set headers
    vraHeader = {"Accept":"application/json","Content-Type":"application/json", "Authorization": "Bearer " + bearer_token}
    snowHeader = {"Accept":"application/json","Content-Type":"application/json", "Authorization": snowCred}
    
    ## Get deployment name from vRA
    vraURIdeployment = vraURI + "deployment/api/deployments/" + deploymentID
    print(vraURIdeployment)
    print("requesting vRA deployment info")
    deploy_r = requests.get(vraURIdeployment,headers=vraHeader,verify=False).json()
    print("results of vra deployment info for Deployment " + deploymentID)
    print (deploy_r)
        
    deploymentName = deploy_r["name"]
    print(str(deploymentName))
    
    ## Find CMDB record's sys_id with the unique DeploymentID
    print("finding the CMDB record...")
    snowURIcmdb = snowURI + "u_cmdb_ci_cloud_instance?sysparm_query=u_unique_id=" + deploymentID
    
    cmdb_q_r = requests.get(snowURIcmdb,headers=snowHeader,verify=False).json()
    print("...")
    print("The CMDB record...")
    print(cmdb_q_r)
    print("...")

    ## PetePincic: code to grab the list of records and extract all unique sys_ids
    snowRows = cmdb_q_r["result"]
    iLen = len(snowRows)
    snowIDs = [""] * iLen
    for i in range(iLen):
        snowIDs[i] = cmdb_q_r["result"][i]["sys_id"]

    #### Sometimes it returns with a list, catch it and move on.
   
    for i in range(iLen):
        snow_id = snowIDs[i]
        ## Use sys_id to update the cmdb record, changing it's state.
        snowURIputCmdb = snowURI + "u_cmdb_ci_cloud_instance/" + snow_id
        print("...")
        print("CMDB Put Payload...")
        cmdb_put_payload = {
    	"u_state":"retired",
    	"u_decom_date": timeStamp
        }
        print(cmdb_put_payload)
        print("...")
        print("CMDB Put Request...")
        update_r = requests.patch(snowURIputCmdb,json=cmdb_put_payload,headers=snowHeader,verify=False).json()
        print("...")
        print(update_r)
    
    ## Create Change record, putting in "Review" state
    print("....")
    print("creating Change Record payload...")
    snowURIcr = snowURI + "change_request"
    cr_payload = {
    	"requested_by":requesterName,
    	"assigned_to":requesterName,
    	"type":"standard",
    	# Use deploymentID as the unique identifier to query on later
        "short_description":"retire: " + deploymentID,
    	"description":"[Automated] Deleting cloud instance(s)",
    	"state":"0"
    }
    print(cr_payload)
    print("....")
    print("posting Change Record...")
    create_cr_r = requests.post(snowURIcr,json=cr_payload,headers=snowHeader,verify=False).json()
    print("results...")
    print(create_cr_r)
    
    ## Query Charnge Record of DeploymentID to find the unique SNOW ID (aka sys_id)
    print("....")
    print("querying Change Record for unique sys_id...")
    snowURIqcr = snowURIcr + "?sysparm_query=short_description=retire:%20" + deploymentID
    q_cr_r = requests.get(snowURIqcr,headers=snowHeader,verify=False).json()
    print("...")
    print("change record info...")
    print(q_cr_r)
    #### Sometimes it returns with a list, catch it and move on.
    try:
        snow_id = q_cr_r["result"][0]["sys_id"]
    except TypeError:
        print("info: type error caught")
        snow_id = q_cr_r["result"]["sys_id"]
        
    print("...")
    print("Unique sys_id is " + snow_id)
    
    ## Use the SNOW ID to Update the Change Record, putting it in a "Closed" state.
    print("....")
    print("building payload to close Change Record...")
    snowURIcloseCR = snowURIcr + "/" + snow_id
    close_cr_payload = {
	"state":"3"
    }
    print(close_cr_payload)
    print("....")
    print("closing the Change Record...")
    close_cr_r = requests.patch(snowURIcloseCR,json=close_cr_payload,headers=snowHeader,verify=False).json()
    print("results...")
    print(close_cr_r)
    print("done")

def get_vRA_Cloud_bearer_token(api_token):
    url = "https://api.mgmt.cloud.vmware.com/iaas/api/login"
    payload = { "refreshToken": api_token }
    result = requests.post(url = url, json = payload)
    result_data = result.json()
    bearer_token = result_data["token"]
    # logging.info("### bearer_token is %s ", bearer_token)
    return bearer_token

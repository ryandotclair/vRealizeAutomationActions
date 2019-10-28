import requests

## This is the vRA ServiceNow Create Workflow Action
## It creates a CMDB record, a Change Record, and Closes the Change Record once done
## Tested on vRA 8.0 / vRA Cloud and SNOW's London release

## Assumptions:
## - A vRA deployment is the trackable unit, and is recorded in the CMDB, regardless of how many 
##   VM's/LBs/Networks are deployed.
## - Only the first IP address that's reported is recorded
## - CMDB table (u_cmdb_ci_cloud_instance) and many custom field names
## - 'requests' is imported, and proper local environments are set (see lines 24-27)


## Known Issue:
## - If the subscription is done against post compute provision, and the blueprint has multiple VM's in it,
##     There will be multiple CMDB/Change records with the same unique identifier used to decommision it.

## Todo:
## - Interrogate the Deployments individual resources and make a CMDB record for each unique resource.

def handler(context, inputs):
    ## Import local environment variables stored in vRA's Actions
    snowURI = inputs["snowURI"]
    snowCred = inputs["snowCred"] #base64 for basic auth
    vraToken = inputs["vraCred"] #requires vRA's api token / bearer token
    vraURI = inputs["vraURI"]
    
    print("inputs")
    
    ## Capture config data from deployment
    deploymentID = inputs["deploymentId"]
    requesterName = inputs["__metadata"]["userName"]
    ipAddr = inputs["addresses"][0] #grabs first IP address
    timeStamp = inputs["__metadata"]["timeStamp"]

    ## Set headers
    vraHeader = {"Accept":"application/json","Content-Type":"application/json", "Authorization":vraToken}
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
    
    ## Create CMDB record
    print("creating CMDB payload...")
    snowURIcmdb = snowURI + "u_cmdb_ci_cloud_instance"
    cmdb_payload = {
        "u_unique_id":deploymentID,
    	"u_state":"active",
    	"u_ip":ipAddr,
    	"u_name":deploymentName,
    	"u_owner":requesterName,
    	"u_vulnerability_group":"vmware-soc",
    	"u_cost_center":"free-beer"
    }
    print(cmdb_payload)
    cmdb_r = requests.post(snowURIcmdb,json=cmdb_payload,headers=snowHeader,verify=False).json()
    print("results...")
    print(cmdb_r)
    
    ## Create Change record, putting in "Review" state
    print("....")
    print("creating Change Record payload...")
    snowURIcr = snowURI + "change_request"
    cr_payload = {
    	"requested_by":requesterName,
    	"assigned_to":requesterName,
    	"type":"standard",
    	# Use deploymentID as the unique identifier to query on later
        "short_description":deploymentID,
    	"description":"[Automated] Deploying cloud instance(s) from Experian's Cloud",
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
    snowURIqcr = snowURIcr + "?sysparm_query=short_description=" + deploymentID
    q_cr_r = requests.get(snowURIqcr,headers=snowHeader,verify=False).json()
    
    #### Sometimes it returns with a list, catch it and move on.
    try:
        snow_id = q_cr_r["result"]["sys_id"]
    except TypeError:
        print("info: type error caught")
        snow_id = q_cr_r["result"][0]["sys_id"]
    
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

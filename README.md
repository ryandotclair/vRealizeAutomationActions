# vRealize Automation Actions
This repository is my collection of vRealize Automation Extensibility Actions. These have been written in Python 3, so should be supported in any FaaS providor.

## Instructions
- Copy the code into a "new" action in vRA. I try to call out what I've tested them against and any known limitations in the comments.
- Any "import" statements at the top need to be added into the Dependency field (on the right side)
- Any "local environment variables" that are called out need to be added as inputs (on the right side)
- Save the action, then go to "Subscriptions"
- Create a subscription, which watches for a particular event, and add the action in question. Optionally you can filter on only certain <blueprints, users, projects, etc> events.

## Available Actions
- `snow-create.py` - A ServiceNow integration, meant to show you can create a CMDB and Change Records for any new deployments
- `snow-retire.py` - A ServiceNow integration, meant to show you can "retire" assets in the CMDB, along with Change Records created with the change.
- `text-me.py` - A texting integration, using twilio (twilio.com) as the texting service. Can notify user when VM has been provisioned along with it's IP address.

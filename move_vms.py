"""
listpds.py - list all VMs that belong to a specific PD in a cluster
eventual goal is to get all of the VMs in the PD, remove those VMs,
then add those VMs to a category which then would be a v3 call to PC
"""

from dataclasses import dataclass
import requests
import urllib3
import argparse
import getpass
import json
from base64 import b64encode
import sys
import os
import time
from requests.auth import HTTPBasicAuth


@dataclass
class RequestParameters:
    """
    dataclass to hold the parameters of our API request
    this is not strictly required but can make
    our requests cleaner
    """
    uri: str
    username: str
    password: str
    payload: list
    method: str


class RequestResponse:
    """
    class to hold the response from our
    requests
    again, not strictly necessary but can
    make things cleaner later
    """

    def __init__(self):
        self.code = 0
        self.message = ""
        self.json = ""
        self.details = ""

    def __repr__(self):
        '''
        decent __repr__ for debuggability
        this is something recommended by Raymond Hettinger
        it is good practice and should be left here
        unless there's a good reason to remove it
        '''
        return (f'{self.__class__.__name__}('
                f'code={self.code},'
                f'message={self.message},'
                f'json={self.json},'
                f'details={self.details})')


class RESTClient:
    """
    the RESTClient class carries out the actual API request
    by 'packaging' these functions into a dedicated class,
    we can re-use instances of this class, resulting in removal
    of unnecessary code repetition and resources
    """

    def __init__(self, parameters: RequestParameters):
        """
        class constructor
        because this is a simple class, we only have a single
        instance variable, 'params', that holds the parameters
        relevant to this request
        """
        self.params = parameters

    def __repr__(self):
        '''
        decent __repr__ for debuggability
        this is something recommended by Raymond Hettinger
        '''
        return (f'{self.__class__.__name__}('
                f'username={self.params.username},password=<hidden>,'
                f'uri={self.params.uri}',
                f'payload={self.params.payload})')

    def send_request(self):
        """
        this is the main method that carries out the request
        basic exception handling is managed here, as well as
        returning the response (success or fail), as an instance
        of our RequestResponse dataclass
        """
        response = RequestResponse()

        """
        setup the HTTP Basic Authorization header based on the
        supplied username and password
        done this way so that passwords are not supplied on the command line
        """
        username = self.params.username
        password = self.params.password
        encoded_credentials = b64encode(
            bytes(f"{username}:{password}", encoding="ascii")
        ).decode("ascii")
        auth_header = f"Basic {encoded_credentials}"

        """
        setup the request headers
        note the use of {auth_header} i.e. the Basic Authorization
        credentials we setup earlier
        """

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"{auth_header}",
            "cache-control": "no-cache",
        }

        try:

            if self.params.method == 'get':
                # submit a GET request
                api_request = requests.get(
                    self.params.uri,
                    headers=headers,
                    auth=HTTPBasicAuth(username, password),
                    timeout=10,
                    verify=False
                )
            elif self.params.method == 'post' or self.params.method == 'put':
                # submit a POST request
                api_request = requests.post(
                    self.params.uri,
                    headers=headers,
                    auth=HTTPBasicAuth(username, password),
                    timeout=10,
                    verify=False,
                    data=self.params.payload
                )
            # if no exceptions occur here, we can process the response
            response.code = api_request.status_code
            response.message = "Request submitted successfully."
            response.json = api_request.json()
            response.details = "N/A"
        except requests.exceptions.ConnectTimeout:
            # timeout while connecting to the specified IP address or FQDN
            response.code = -99
            response.message = f"Connection has timed out."
            response.details = "Exception: requests.exceptions.ConnectTimeout"
        except urllib3.exceptions.ConnectTimeoutError:
            # timeout while connecting to the specified IP address or FQDN
            response.code = -99
            response.message = f"Connection has timed out."
            response.details = "urllib3.exceptions.ConnectTimeoutError"
        except requests.exceptions.MissingSchema:
            # potentially bad URL
            response.code = -99
            response.message = "Missing URL schema/bad URL."
            response.details = "N/A"
        except Exception as _e:
            """
            unhandled exception
            ... don't do this in production
            """
            response.code = -99
            response.message = "An unhandled exception has occurred."
            response.details = _e

        return response


# get the time the script started
start_time = time.time()

"""
suppress warnings about insecure connections
you probably shouldn't do this in production
"""
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

"""
setup our command line parameters
for this example we only require the a single parameter
- the name of the JSON file that contains our request parameters
this is a very clean way of passing parameters to this sort of
script, without the need for excessive parameters on the command line
"""
parser = argparse.ArgumentParser()
parser.add_argument("json", help="listparms")
args = parser.parse_args()

"""
try and read the JSON parameters from the supplied file
"""
json_data = ""
try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    with open(f"{script_dir}/{args.json}", "r") as params:
        json_data = json.load(params)
    cluster_ip = json_data["cluster_ip"]
    pc_ip = json_data["pc_ip"]
    protection_domain = json_data["pd"]
    category = json_data["category"]
    user = json_data["username"]
except FileNotFoundError:
    print(f"{args.json} parameters file not found.")
    sys.exit()
except json.decoder.JSONDecodeError:
    print("\nThe provided JSON file cannot be parsed.")
    print("Please check the file contains valid JSON, then try again.\n")
    sys.exit()
except KeyError:
    print('Required key was not found in the specified JSON parameters file.  Exiting ...')
    sys.exit()

#######################################
# gather some info before carrying on #
#######################################

# for this test script we're just going to assume both PE and PC authenticate as 'admin'
print(f'\nUsername: {user}')
print(f'Protection Domain: {protection_domain}')
print(f'Category: {category}\n')

# get the cluster password
cluster_password = getpass.getpass(
    prompt="Please enter your cluster password: ", stream=None
)
# get the PC password
pc_password = getpass.getpass(
    prompt="Please enter your Prism Central password: ", stream=None
)

print(f'\nGetting entities that belong to PD named {protection_domain} ...')
# setup the parameters for the initial request
parameters = RequestParameters(
    uri=f"https://{cluster_ip}:9440/api/nutanix/v2.0/protection_domains/{protection_domain}",
    username=user,
    password=cluster_password,
    payload=[],
    method='get'
)
rest_client = RESTClient(parameters)
# get the entities that belong to the specified PD
get_pd_entities_response = rest_client.send_request()

"""
check that the first request was successful
if it wasn't, there's no point continuing as it means later requests will also fail
"""

if get_pd_entities_response.code == -99:
    print(get_pd_entities_response.message)
    print(get_pd_entities_response.details)
    sys.exit()

##############################################
# see if there are any entities to work with #
# if there aren't, there's no point going    #
# any further                                #
##############################################

vm_count = len(get_pd_entities_response.json['vms'])
if vm_count == 0:
    print(f'PD {protection_domain} has no existing entities.  Nothing to do.')
    sys.exit()
elif vm_count == 1:
    print(f'\n1 VM will be reconfigured.\n')
else:
    print(f'\n{vm_count} VMs will be reconfigured.\n')

"""
create the list containing all VM names and UUIDs
these VMs are existing members of the specified PD
"""
vm_names = []
vm_details = []
for vm in get_pd_entities_response.json['vms']:
    vm_names.append(vm['vm_name'])
    vm_details.append({'uuid': vm['vm_id'], 'name': vm['vm_name']})

##############################
# delete the VMs from the PD #
##############################

# at this point we have confirmed there is at least 1 VM in the PD
remove_vm_parameters = RequestParameters(
    uri=f'https://{cluster_ip}:9440/api/nutanix/v2.0/protection_domains/{protection_domain}/unprotect_vms',
    username=user,
    password=cluster_password,
    payload=json.dumps(vm_names),
    method='post'
)
rest_client = RESTClient(remove_vm_parameters)
print(f'Removing VMs from PD {protection_domain} ...')
remove_response = rest_client.send_request()
print('Done.\n')

###############################
# add the VMs to the category #
###############################

"""
for each of the VMs in the PD we now need to do a few things
we need to add the spec, the api_version and the metadata to the individual VM payload
then add the category information to the individual VM payload
the final step is to add the VM payload to the api_request_list of the main PUT payload
"""

"""
start building the PUT request payload
this first batch request will get info about all VMs in the PD
"""
get_vm_info_put_payload = {
    "action_on_failure": "CONTINUE",
    "execution_order": "SEQUENTIAL",
    "api_request_list": [],
    "api_version": "3.0"
}

"""
build the payload for getting each VM's info
it is cleaner to do this with the batch API than "manually" running individual vms API requests
"""
for vm in vm_details:
    # get the VM info
    vm_info_payload = {
        'operation': 'GET',
        'path_and_params': f'/api/nutanix/v3/vms/{vm["uuid"]}'
    }
    get_vm_info_put_payload['api_request_list'].append(vm_info_payload)

# setup the request parameters
vm_info_parameters = RequestParameters(
    uri=f'https://{pc_ip}:9440/api/nutanix/v3/batch',
    username=user,
    password=pc_password,
    payload=json.dumps(get_vm_info_put_payload),
    method='post'
)
rest_client = RESTClient(vm_info_parameters)
# send the request
print(f'Running batch request to get VM info ...')
info_response = rest_client.send_request()
print('Done.\n')

# extract the category name and value from the value specified via JSON parameters file
category_name = category.split(':')[0]
category_value = category.split(':')[1]

# build the categories part of the PUT request payload
category_payload = {f'{category_name}': f'{category_value}'}

"""
start building the PUT request payload
this second batch request will add the VMs to the specified category
"""
update_vm_category_put_payload = {
    "action_on_failure": "CONTINUE",
    "execution_order": "SEQUENTIAL",
    "api_request_list": [],
    "api_version": "3.0"
}

"""
now that we have spec, metadata etc for each VM in the PD,
we can construct the batch request to add each of those VMs
to the specified category
"""
print(f'Building batch request payload before updating categories ...')
for api_response in info_response.json['api_response_list']:
    update_vm_payload = {
        'operation': 'PUT',
        'path_and_params': f'{api_response["path_and_params"]}',
        'body': {}
    }
    update_vm_payload['body']['spec'] = api_response['api_response']['spec']
    update_vm_payload['body']['api_version'] = api_response['api_response']['api_version']
    update_vm_payload['body']['metadata'] = api_response['api_response']['metadata']
    update_vm_payload['body']['metadata']['categories'] = category_payload
    update_vm_category_put_payload['api_request_list'].append(update_vm_payload)
print('Done.\n')

# setup the request parameters
vm_update_parameters = RequestParameters(
    uri=f'https://{pc_ip}:9440/api/nutanix/v3/batch',
    username=user,
    password=pc_password,
    payload=json.dumps(update_vm_category_put_payload),
    method='post'
)
rest_client = RESTClient(vm_update_parameters)
# send the request
print(f'Adding VMs to category "{category_name}:{category_value}" ...')
update_response = rest_client.send_request()
print('Done.\n')

# format and display the results of the batch request
for api_response in update_response.json['api_response_list']:
    print(f"HTTP code {api_response['status']} | State {api_response['api_response']['status']['state']} | VM {api_response['api_response']['spec']['name']}")

print('\nAll operations finished (%.2f seconds)' % (time.time() - start_time))

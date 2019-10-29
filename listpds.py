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

    def get_request(self):
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
            # submit the request
            api_request = requests.get(
                self.params.uri,
                headers=headers,
                auth=HTTPBasicAuth(username, password),
                timeout=30,
                verify=False
            )
            # if no exceptions occur here, we can process the response
            response.code = api_request.status_code
            response.message = "Request submitted successfully."
            response.json = api_request.json()
            response.details = "N/A"
        except requests.exceptions.ConnectTimeout:
            # timeout while connecting to the specified IP address or FQDN
            response.code = -99
            response.message = f"Connection has timed out. {username} {password}"
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
except FileNotFoundError:
    print(f"{args.json} parameters file not found.")
    sys.exit()
except json.decoder.JSONDecodeError:
    print("\nThe provided JSON file cannot be parsed.")
    print("Please check the file contains valid JSON, then try again.\n")
    sys.exit()

try:
    cluster_ip = json_data["cluster_ip"]
    protection_domain = json_data["pd"]
    user = json_data["username"]
    print(f"username {user}")
    # get the cluster password
    print(f"\nConnecting to {cluster_ip} ...")
    cluster_password = getpass.getpass(
        prompt="Please enter your cluster password: ", stream=None
    )
    print(f"password {cluster_password}")
    print(f"https://{cluster_ip}:9440/api/nutanix/v2.0/protection_domains/{protection_domain}")
    # setup the parameters for the initial request
    parameters = RequestParameters(
        uri=f"https://{cluster_ip}:9440/api/nutanix/v2.0/protection_domains/{protection_domain}",
        username=user,
        password=cluster_password
    )
    """
    this instance of our RESTClient class will be used for this and
    all subsequent requests, if they are required
    i.e. if the cluster has >500 VMs
    """
    rest_client = RESTClient(parameters)
    # send the initial request
    response1 = rest_client.get_request()

    vmlist = []
    vmlist = response1.json['vms']

    vmnames = []
    for d in vmlist:
        vminpd = d['vm_name']
        vmnames.append(vminpd)

    print(vmnames)
    sys.exit()
except Exception as ex:
    print(ex)
finally:
    sys.exit()

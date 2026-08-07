#! /usr/bin/env python3

import argparse
import json
import os
import socket

import requests
import urllib3
from environs import env
from requests.auth import HTTPBasicAuth

"""
Most of the webMethods api detail for the main process was provided through a Safari Google search for help writing 
a Python process to interact with a webMethods integration server, primarily for this exact process, to import packages  
following some kind of more automated process than using the standard wM Administrator ui. We added the use of argparse 
for some command-line arguments and environs for following a more standard practice of using a separate file for the 
more serious user accounts and passwords as well as some standard constants like the server name, port, and others.
We realize there is lots of ci/cd process missing just having a basic Python file that imports packages using the 
standard wM zip format. Most current wM ci/cd workflows use GitHub for managing the entire package in a standard 
package file system layout, an artifact application like Artifactory, and a ci/cd application like Jenkins.
This accesses one or more wM archive zip files on a local file system where the script runs, but we are more used to 
deploying files from the replicate/inbound directory on the host integration server.
"""

# Alternative for obtaining the current directory, this one using os
# Environs then reads the contents of the specified file, where this naming is nonstandard
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env.read_env(os.path.join(BASE_DIR, 'conf', 'wmcontroller.cnf'))

# Now set the variables (constants) including the following. Defaults are set in this file as follows,
#   and the settings in the *.cnf file override any defaults.
auth_user = env.str('AUTH_USER')
auth_passwd = env.str('AUTH_PASSWD')
Debug = env.bool('DEBUG', default=False)
import_source = env.str('IMPORT_SOURCE')
inbound_directory = env.str('INBOUND_DIRECTORY')
protocol = env.str('PROTOCOL', default='https')
port = env.int('PORT', default=5543)
server = env.str('SERVER')
ssl_certificate_verification = env.bool('VERIFY_SSL_CERTIFICATE', default=True)

client = None
import_file = None
response = None

# Check the source running this process, for now we would rather run this from the actual integration server.
host_name = str(socket.gethostname()).lower()

# Create an argument parser object for checking user input
parser = argparse.ArgumentParser()

# Define the arguments to allow for flexibility
parser.add_argument('-i', '--import_file', nargs='?', const='')

# Parse the user's arguments in sys.args according to the rules and arguments that we've defined
args = parser.parse_args()

if Debug:
    print(f'DEBUG:args is {args}, Namespace type is type({args.__dict__})')
    print(f"Client host is {host_name}.\n")

if args.import_file:
    import_file = args.import_file
    print(f'Trying the import using file {import_file}.')
else:
    print(f'You did not provide an import file, exiting.')
    exit(1)


def integration_server_status(server):
    """
    This function checks integration server status prior to attempting the import. While the process in main will 
    certainly error out in the event the server is not responsive, we're trying to have something that is a bit more 
    graceful and reflects all possible outcomes that we've seen before.
    The print statements in the exception block should probably log or print to stderr, but for now we'll admit to not 
    having this set up with logging.
    """

    # Suppress SSL warnings if using self-signed certificates
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        'Accept': 'application/json',
    }

    params = {
        'expand': 'true',
    }

    response = None

    try:
        response = requests.get(
            f'{protocol}://{server}:{port}/admin/package',
            params=params,
            headers=headers,
            auth=(auth_user, auth_passwd),
            timeout=10,
            verify=ssl_certificate_verification,  # note this generates a warning
        )
    except requests.ConnectionError as e:
        if 'HTTPSConnectionPool' in str(e):
            print(f"\nException: {e}\nHTTPSConnectionPool error on server: {server}. The integration server is not "
                  f"running.\n")
        elif 'NewConnectionError' in str(e):
            print(f"\nException: {e}\nNewConnectionError on server: {server}. The integration server is not running.\n")
        elif 'ConnectTimeoutError' in str(e):
            print(f"\nException: {e}\nConnectTimeout on server: {server}. The integration server is not running, " \
                  f"busy, or not accepting connections.\n")
        elif 'ConnectionResetError' in str(e):
            print(f"\nException: {e}\nConnectionError on server: {server}. The integration server may be in the " \
                  f"process of starting up or shutting down.\n")
        if Debug:
            print(f"\nIS Status Check returning error, Type: {type(e)}, {e}\n")
        # exit(1)

    if not response:
        return ('None', f'no response from the integration server')
    elif response.status_code == 200:
        return (response.status_code, f'the integration server is up and responding as expected')


response_status_code, response_text = integration_server_status(server)

if response_status_code == 200:
    print(f'\nThe integration server returned a {response_status_code}, indicating {response_text}.\n')
elif response_status_code == 'None':
    print(f'The integration server did not return a http status code, suggesting there was no response from the '
          f'server.\n')
    exit(1)
else:
    print(f'The integration server check returned "{response_text}".')
    exit(1)

# Suppress SSL warnings if using self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# List of local paths to your custom package zip archives
# PACKAGES_TO_IMPORT = [
#     r"C:\migration\MyCustomBilling.zip",
#     r"C:\migration\ERPIntegration.zip"
# ]

with open(os.path.join(import_source, import_file), "r", encoding="utf-8") as f:
    packages_to_import = json.load(f)["files"]
    print("The import file contains the following packages:")
    for one_package in packages_to_import:
        print(one_package)
    print()

# Base URL for package administration actions
URL = f"https://{server}:{port}/admin/packages"
PARAMS = {"action": "import"}

# Initialize authenticated session
session = requests.Session()
session.auth = HTTPBasicAuth(auth_user, auth_passwd)
# Do NOT manually set Content-Type header to application/json;
# requests handles the multipart boundary header automatically when using the files parameter.
session.headers.update({"Accept": "application/json"})

# --- EXECUTION ---
print("Starting the webMethods package deployment/import using Python and the wM api ...")

for package in packages_to_import:  # package was package_path, packages_to_import is a list
    print("-" * 50)

    # Construct the same form of the full file path identifier, including the file name as above, the example is
    # r"C:\migration\MyCustomBilling.zip"
    absolute_package_path = f'r"{import_source}/{package}"'
    if Debug:
        print(f'Full path and package name is {absolute_package_path}.')

    if not os.path.exists(absolute_package_path):
        print(f"ERROR: Local file not found at {absolute_package_path}, checking for other packages to import.")
        continue

    file_name = os.path.basename(absolute_package_path)
    print(f"Uploading and importing: {file_name} ...")

    try:
        # Open binary file pointer for multipart upload
        with open(package, 'rb') as package_file:
            # Construct form payload mapping 'file' keyword to the file object
            files = {
                'file': (file_name, package_file, 'application/zip')
            }

            # Execute POST request. Turn verify=True if production SSL certs are bound
            response = session.post(URL, params=PARAMS, files=files, verify=False, timeout=60)

            # Evaluate deployment response code
            if response.status_code == 200:
                print(f"SUCCESS: {file_name} imported successfully on the integration server.")
            else:
                print(f"FAILED: Import rejected for {file_name}.")
                print(f"HTTP Status Code: {response.status_code}")
                print(f"Server Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"NETWORK ERROR: Connection failed during package transfer.")
        print(f"Details: {e}")

print("-" * 50)
print("The import process ran to completion, but errors may have occurred during the import. Please check the "
      "integration server and verify the packages are active. If this is the first deployment of a package to a "
      "server, additional actions may be required, such as adding users and setting up ACLs, global variables, allowed "
      "write paths, and other non-package functionality.")

#! /usr/bin/env python3

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

import argparse
import json
import os

import requests
import urllib3
from environs import env
from requests.auth import HTTPBasicAuth


# Original start of code moved to main


def integration_server_status(target_server):
    """
    This function checks integration server status prior to attempting the import. While the process in main will
    certainly error out in the event the server is not responsive, we're trying to have something that is a bit more
    graceful and reflects all possible outcomes that we've seen before. The print statements in the except block
    should probably log or print to stderr, but for now we'll admit to not having this set up with logging. This is a
    new feature in the MSR which may not be present in normal integration server. Reference is
    https://www.ibm.com/docs/en/webmethods-integration/wm-integration-server/12.1.0?topic=guide-monitoring
    -microservices-runtime
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
            f'{protocol}://{target_server}:{port}/health',
            params=params,
            headers=headers,
            auth=(auth_user, auth_passwd),
            timeout=10,
            verify=ssl_certificate_verification,  # note this generates a warning
        )
    except requests.ConnectionError as e:
        if 'HTTPSConnectionPool' in str(e):
            print(f"\nException: {e}. HTTPSConnectionPool error on server: {target_server}. The integration "
                  f"server is not running.\n")
        elif 'NewConnectionError' in str(e):
            print(f"\nException: {e}\nNewConnectionError on server: {target_server}. The integration server is "
                  f"not running.\n")
        elif 'ConnectTimeoutError' in str(e):
            print(f"\nException: {e}\nConnectTimeout on server: {target_server}. The integration server is not "
                  f"running, busy, or not accepting connections.\n")
        elif 'ConnectionResetError' in str(e):
            print(f"\nException: {e}\nConnectionError on server: {target_server}. The integration server may be "
                  f"in the process of starting up or shutting down.\n")
        if Debug:
            print(f"\nIS Status Check returning error, Type: {type(e)}, {e}\n")
        # exit(1)

    if not response:
        return 'None', f'no response from the integration server'
    elif response.status_code == 200:
        if Debug:
            print(f'{response}')
        return response.status_code, f'the integration server is up and responding as expected'
    elif response.status_code == 503:
        return response.status_code, f'the integration server responded, but one of the health indicators returned a DOWN status'


# change this to a function like verify_package_import
def verify_package_import(imported_package_name):

    VERIFICATION_URL = f"https://{integration_server}:{port}/wm.server.packages/packageList"

    package_name, suffix = imported_package_name.split(sep=".")

    try:

        verification_response = session.post(VERIFICATION_URL, verify=False, timeout=60)

        if verification_response.status_code == 200:
            post_import_package_list = verification_response.json()
            updated_packages = post_import_package_list.get("updated_packages", [])

            target_pkg = next((p for p in updated_packages if p.get("name") == PACKAGE_NAME), None)

            if target_pkg:
                # Check the specific boolean status keys mapped by the webMethods core
                is_enabled = target_pkg.get("enabled", False)

                if is_enabled:
                    print(f"Verification Successful: {PACKAGE_NAME} is Active and Enabled.")
                else:
                    print(f"Warning: {PACKAGE_NAME} was imported, but is currently INACTIVE or DISABLED. Check for "
                          f"problems such as dependencies.")
            else:
                print(f"Error: {PACKAGE_NAME} was not found in the package list.")
        else:
            print(f"Verification request failed with status: {response.status_code}.")

    except Exception as e:
        print(f"Failed to run import verification: {e}")


# Original location of calling integration server status


# Converted this to a function, where it was more or less the main before
def import_webmethods_packages(package_list) -> list:
    # Suppress SSL warnings if using self-signed certificates
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Original location of open import file, replacing with a list

    # Original Base URL and PARAMS

    # Original session location inside this function

    IMPORT_URL = f"https://{integration_server}:{port}/pub.packages/installPackage"

    # --- EXECUTION ---
    print("Starting the webMethods package deployment/import using Python and the wM api ...")

    for package in package_list:
        print("-" * 50)

        PARAMS = {
            "packageFile": "{package}",
            "activateOnInstall": "yes",
            "archiveOnInstall": "yes",
        }

        try:

            # Execute POST request. Turn verify=True if production SSL certs are bound
            import_response = session.post(IMPORT_URL, params=PARAMS, verify=False, timeout=60)

            if import_response.status_code != 200:
                print(f"FAILED: Problem on {package} import.")
                print(f"http Status Code: {import_response.status_code}")
                print(f"Server Response on Import: {import_response.text}")
                print()

                # moved verify import from here

            # Evaluate deployment response code
            else:
                print(f"SUCCESS: {package} imported successfully on the integration server.")
                print(f"Server Response on Import: {import_response.text}")
                print(f"Running verification process ... \n")
                verify_package_import(package)
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Import failed or other problem.")
            print(f"Details: {e}")

    print("-" * 50)
    print("The import process ran to completion, but errors may have occurred during the import. Please check the "
          "integration server and verify the packages are active. If this is the first deployment of a package to a "
          "server, additional actions may be required, such as adding users and setting up ACLs, global variables, "
          "allowed write paths, and other non-package functionality.")


if __name__ == '__main__':

    # Alternative for obtaining the current directory, this one using os
    # Environs then reads the contents of the specified file, where this naming is nonstandard
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    env.read_env(os.path.join(BASE_DIR, 'conf', 'wm_api_example.cnf'))

    # Now set the variables (constants) including the following. Defaults are set in this file as follows,
    #   and the settings in the *.cnf file override any defaults.
    auth_user = env.str('AUTH_USER')
    auth_passwd = env.str('AUTH_PASSWD')
    Debug = env.bool('DEBUG', default=False)
    import_source = env.str('IMPORT_SOURCE')
    inbound_directory = env.str('INBOUND_DIRECTORY')
    protocol = env.str('PROTOCOL', default='https')
    port = env.int('PORT', default=5543)
    integration_server = env.str('INTEGRATION_SERVER')
    ssl_certificate_verification = env.bool('VERIFY_SSL_CERTIFICATE', default=True)

    # Create an argument parser object for checking user input
    parser = argparse.ArgumentParser()

    # Define the arguments to allow for flexibility
    parser.add_argument('-i', '--import_file', nargs='?', const='')

    # Parse the user's arguments in sys.args according to the rules and arguments that we've defined
    args = parser.parse_args()

    if Debug:
        print(f'DEBUG:args is {args}, Namespace type is type({args.__dict__})')

    if args.import_file:
        import_file = args.import_file
        print(f'\nInitializing the import using file {import_file}.')
    else:
        print(f'You did not provide an import file, exiting.')
        exit(1)

    response_status_code, response_text = integration_server_status(integration_server)

    if response_status_code == 200:
        print(f'\nThe integration server returned a {response_status_code}, {response_text}.\n')
    elif response_status_code == 'None':
        print(f'The integration server did not return a http status code, suggesting there was no response from the '
              f'server.\n')
        exit(1)
    else:
        print(f'The integration server check returned "{response_text}".')
        exit(1)

    # Initialize an authenticated session here, which the status check should probably use
    session = requests.Session()
    session.auth = HTTPBasicAuth(auth_user, auth_passwd)
    # Do NOT manually set Content-Type header to application/json;
    # requests handles the multipart boundary header automatically when using the files parameter.
    session.headers.update({"Accept": "application/json"})

    with open(import_file, "r", encoding="utf-8") as f:
        packages_to_import = json.load(f)["files"]
        print("The import file contains the following packages:")
        for one_package in packages_to_import:
            print(one_package)
        print()

        if Debug:
            print()
            print(f"Sending this list of packages to the import process:")
            print(packages_to_import)
            print()

    import_webmethods_packages(packages_to_import)

    # close the session and exit
    session.close()
    exit(0)

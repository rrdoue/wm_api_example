#! /usr/bin/env python3

import os
import json
import argparse

from bs4 import BeautifulSoup
import requests
import urllib3
from environs import env
from requests.auth import HTTPBasicAuth


# ==========================================
# 1. STANDALONE WORKER FUNCTIONS
# ==========================================

def integration_server_status(target_server, port, auth_user, auth_passwd, protocol, ssl_verification=False):
    """Checks the independent MSR /health endpoint. Returns True if 200, else False."""
    if not ssl_verification:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {'Accept': 'application/json'}
    params = {'expand': 'true'}
    url = f'{protocol}://{target_server}:{port}/health'

    try:
        response = requests.get(url, params=params, headers=headers, auth=(auth_user, auth_passwd), timeout=10,
                                verify=ssl_verification)
        if response.status_code == 200:
            print(f"SUCCESS: The integration server {target_server} is up and healthy.")
            return True
        elif response.status_code == 503:
            print(f"WARNING: The integration server {target_server} responded, but a health indicator is DOWN.")
            return False
        return False
    except requests.exceptions.RequestException as e:
        print(f"\nCONNECTION ERROR: Could not connect to {target_server}. Error: {e}\n")
        return False


def import_webmethods_package(session, integration_server, port, package_name, protocol):
    """Handles ONLY the isolated upload/import of a single package string."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    IMPORT_URL = f"{protocol}://{integration_server}:{port}/pub.packages/installPackage"
    PARAMS = {
        "packageFile": f"{package_name}",
        "activateOnInstall": "yes",
        "archiveOnInstall": "yes",
    }

    try:
        response = session.post(IMPORT_URL, params=PARAMS, verify=False, timeout=60)
        if response.status_code == 200:
            print(f"SUCCESS: {package_name['name']} imported successfully.")
            return True

        # package_name appears to be equivalent to a Python dictionary and elements can be called with the keys
        # beautifulsoup4 allows one to retrieve the text response from response.text
        # So integration server correctly returns a 404, Not Found error, and probably others as appropriate

        response_text = BeautifulSoup(response.text, "html.parser")
        import_response_text = response_text.find("b").get_text()
        print(f"FAILED: Status {response.status_code} for {package_name['name']} import. Response: "
              f"{import_response_text}.")
        return False

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Import API request failed for {package_name['name']}: {e}")
        return False


def verify_package_import(session, integration_server, port, package_name, protocol):
    """
    This function accepts a webMethods zip file package name and verifies whether the package is active on the
    integration server.
    Input: package file name, for example, Gne_NonValUtils.zip
    Output: The package's status on the integration server, that is, Enabled or Disabled, but in the form True or False.
            In addition, output includes the package name and a text version of the verification used in the summary.
    """

    VERIFICATION_URL = f"{protocol}://{integration_server}:{port}/admin/package?expand=true"

    is_wmpackage_enabled = None
    wmpackage = None

    # package_name is really a package file information structure like a dictionary, where 'name' is the package zip
    # file name including the file-type suffix
    wmpackage, suffix = package_name['name'].split(".")

    try:
        response = session.get(VERIFICATION_URL, verify=False, timeout=60)
        if response.status_code == 200:

            wm_packages_dict = response.json()

            # This dictionary comprehension creates a dictionary of package names and the enabled field for faster
            # lookups
            is_wmpackage_enabled = \
                {wm_package["packageName"]: wm_package["enabled"] for wm_package in wm_packages_dict["packages"]}

            if is_wmpackage_enabled.get(wmpackage) == 'true':
                print(f"Verification Successful: {wmpackage} is Active and Enabled.")
                return True, wmpackage, f"(Verification Successful) {wmpackage} is Active and Enabled."
            elif is_wmpackage_enabled.get(wmpackage) == 'false':
                print(f"Warning: {wmpackage} is INACTIVE or DISABLED.")
                return False, wmpackage, f"(Warning) {wmpackage} is INACTIVE or DISABLED."
            else:
                print(f"Warning: {wmpackage} not found.")
                return False, wmpackage, f"(Warning) {wmpackage} not found."
            return False
    except Exception as e:
        print(f"Failed to run package checklist validation for {package_name}: Status Code: {response.status_code}. \n"
              f"Error: {e}\n")
        return False


# ==========================================
# 2. MAIN SYSTEM ORCHESTRATOR
# ==========================================

if __name__ == '__main__':

    post_verification_dict = {}

    # Configuration setup environment parsers
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    env.read_env(os.path.join(BASE_DIR, 'conf', 'wm_api_example.cnf'))

    auth_user = env.str('AUTH_USER')
    auth_passwd = env.str('AUTH_PASSWD')
    debug = env.bool('DEBUG', default=False)
    protocol = env.str('PROTOCOL', default='https')
    port = env.int('PORT', default=5543)
    integration_server = env.str('INTEGRATION_SERVER')
    ssl_certificate_verification = env.bool('VERIFY_SSL_CERTIFICATE', default=True)

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--import_file', nargs='?', const='')
    args = parser.parse_args()

    if not args.import_file:
        print('You did not provide a JSON-formatted import manifest file, exiting.')
        exit(1)

    with open(args.import_file, "r", encoding="utf-8") as f:
        packages_to_import = json.load(f)["files"]

    # --- STEP 1: Standalone Server Pre-Flight Check ---
    if not integration_server_status(integration_server, port, auth_user, auth_passwd, protocol,
                                     ssl_certificate_verification):

        print("Aborting pipeline import process, integration server health metrics failed.\n")
        exit(1)

    # --- STEP 2: Scoped Loop Execution Management ---
    session = requests.Session()
    session.auth = HTTPBasicAuth(auth_user, auth_passwd)
    session.headers.update({"Accept": "application/json"})

    # print(f"\nStarting deployment queue processing for {len(packages_to_import)} packages ...\n")
    print(f"\nStarting the webMethods package import process consisting of {len(packages_to_import)} packages using "
          f"Python and the wM api ...")
    for zip_file in packages_to_import:
        print(zip_file['name'])
    print()

    try:
        for package in packages_to_import:
            print("-" * 60)

            # Action A: Call isolated upload
            is_imported = import_webmethods_package(session, integration_server, port, package, protocol)

            # Action B: Call independent verification loop ONLY if deployment response accepted
            if is_imported:
                verification_status, package_name, verification_text = verify_package_import(session, integration_server, port, package, protocol)
                post_verification_dict[package_name] = verification_text

        print("-" * 60)
        # Note: if either the import or verification function returns False, the following is not true, resolve this
        print("\nAll pipeline tasks ran to completion.\n")

        for key, value in post_verification_dict.items():
            print(f"{key}: {value}")
        print()
    finally:
        session.close()

#! /usr/bin/env python3

"""
This script accesses one or more wM archive zip files, for now located in the traditional <webmethods_home>/IntegrationServer/replicate/inbound directory on the host integration server's local filesystem. The input file, including its full path, is a json-formatted list of webMethods zip files. For now, the json-formatted file is a list of files documented as a Python dictionary including the zip file name and a file-type description. 
Most of the webMethods api detail for the main process was provided through a Safari Google search for help writing a Python process to interact with a webMethods integration server, primarily for this exact process, to import packages following some kind of more automated process than using the standard wM Administrator ui. We added the use of argparse for some command-line arguments and environs for following a more standard practice of using a separate file for the more serious user accounts and passwords as well as some standard constants like the server name, port, and others.
We realize there is lots of ci/cd process missing just having a basic Python file that imports packages using the standard wM zip format. Most current wM ci/cd workflows use GitHub for managing the entire package in a standard package file system layout, an artifact application like Artifactory, and a ci/cd application like Jenkins.
Input: -i (--import_file) *.json file, example file in the GitHub repository at documentation/design/file_formats/wm-import-files-metadata.json
Output: Informational progress lines and a summary result, all to stdout
"""

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


def integration_server_status(
    target_server, port, auth_user, auth_passwd, protocol, ssl_verification=False
):
    """
    Checks the independent webMethods Microservices Runtime (MSR) /health endpoint. Returns True if 200, else False. The original version had lots of explanatory error checks, but this one is a simplified version. The health uri has lots of options for checking different aspects of the integration server MSR. This is a simplified first implementation. In more controlled environments, where we are accustomed to suspending processing and disabling jdbc adapters and other functionality during a deployment, this version will most likely return a False response, ending the operation with no action taken.
    """

    if not ssl_verification:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {"Accept": "application/json"}
    params = {"expand": "true"}
    url = f"{protocol}://{target_server}:{port}/health"

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            auth=(auth_user, auth_passwd),
            timeout=10,
            verify=ssl_verification,
        )
        if response.status_code == 200:
            print(f"SUCCESS: The integration server {target_server} is up and healthy.")
            return True
        elif response.status_code == 503:
            print(
                f"WARNING: The integration server {target_server} responded, but a health indicator is DOWN."
            )
            return False
        return False
    except requests.exceptions.RequestException as e:
        print(f"\nCONNECTION ERROR: Could not connect to {target_server}. Error: {e}\n")
        return False


def import_webmethods_package(
    session, integration_server, port, package_name, protocol
):
    """
    Executes the webMethods import functionality for a single package. The package name passed around is really a package file information structure that resembles  a dictionary, where 'name' is the package zip file name, including the zip suffix. From all information, calling the url returns a http 200 status code, but not yet sure whether there is a response.text. It might be wise to write the function so it tries to return any text. Unsuccessful responses throw status codes consistent with ietf standards.
    Input: http session and other url parameters.
    Output: Boolean True/False, webMethods package file name, text response 
    """

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    IMPORT_URL = f"{protocol}://{integration_server}:{port}/pub.packages/installPackage"
    PARAMS = {
        "packageFile": f"{package_name["name"]}",
        "activateOnInstall": "yes",
        "archiveOnInstall": "yes",
    }

    # package_name is a converted Python dictionary where elements can be called with the keys
    # package_name is really a package file information structure like a dictionary, where 'name' is the package zip
    #    file name including the file-type suffix. Note the name value must be used above in the parameters.
    wmpackage, suffix = package_name["name"].split(".")

    # beautifulsoup4 allows one to retrieve the text response from response.text
    # So integration server correctly returns a 404, Not Found error, and probably others as appropriate

    try:
        response = session.post(IMPORT_URL, params=PARAMS, verify=False, timeout=60)

        if response.status_code == 200:
            response_text = BeautifulSoup(response.text, "html.parser")
            import_response_text = response_text.find("b").get_text()

            print(f"SUCCESS: {package_name['name']} was imported successfully.")

            if not import_response_text:
                import_response_text = (
                    f"SUCCESS: {package_name['name']} was imported successfully."
                )
            return True, wmpackage, import_response_text

        else:
            response_text = BeautifulSoup(response.text, "html.parser")
            import_response_text = response_text.find("b").get_text()
            print(
                f"(FAILED) Status {response.status_code} for {package_name['name']} import. Response: "
                f"{import_response_text}."
            )
            return (
                False,
                wmpackage,
                f"(FAILED) Status {response.status_code} for {package_name['name']} import. "
                f"Response: {import_response_text}.",
            )

    except requests.exceptions.RequestException as e:
        print(f"(ERROR) http import request failed for {package_name['name']}: {e}")
        return (
            False,
            wmpackage,
            f"(ERROR) http import request failed for {package_name['name']}: {e}",
        )


def verify_package_import(session, integration_server, port, package_name, protocol):
    """
    This function accepts a webMethods zip file package name and verifies whether the package is active on the integration server. Called after the import package function, we expect the package to be in an Enabled state.
    Input: package_name, for example, Gne_NonValUtils.zip. However, it is not in a simple form usually provided to  the integration server. Note this was a result of the json file implementation read by the overall process. Other inputs include http session and other associated url parameters.
    Output: Boolean True/False, package_name, and a more standard webMethods text representation of the package's status on the integration server, for example, Enabled or Disabled and Active or Inactive.
    """

    VERIFICATION_URL = (
        f"{protocol}://{integration_server}:{port}/admin/package?expand=true"
    )

    # noinspection PyUnusedLocal
    is_wmpackage_enabled: dict = {}
    # noinspection PyUnusedLocal
    wmpackage = None

    # package_name appears to be equivalent to a Python dictionary and elements can be called with the keys
    # package_name is really a package file information structure like a dictionary, where 'name' is the package zip
    #    file name including the file-type suffix
    wmpackage, suffix = package_name["name"].split(".")

    try:
        response = session.get(VERIFICATION_URL, verify=False, timeout=60)
        if response.status_code == 200:
            wm_packages_dict = response.json()

            # This dictionary comprehension creates a dictionary of package names and the enabled field for faster
            #    lookups
            is_wmpackage_enabled = {
                wm_package["packageName"]: wm_package["enabled"]
                for wm_package in wm_packages_dict["packages"]
            }

            if is_wmpackage_enabled.get(wmpackage) == "true":
                print(f"Verification Successful: {wmpackage} is Active and Enabled.")
                return (
                    True,
                    wmpackage,
                    f"(Verification Successful) {wmpackage} is Active and Enabled.",
                )
            elif is_wmpackage_enabled.get(wmpackage) == "false":
                print(f"Warning: {wmpackage} is INACTIVE or DISABLED.")
                return (
                    False,
                    wmpackage,
                    f"(Warning) {wmpackage} is INACTIVE or DISABLED.",
                )
            else:
                print(f"Warning: {wmpackage} not found.")
                return False, wmpackage, f"(Warning) {wmpackage} not found."
    except Exception as e:
        print(
            f"Failed to run package verification for {package_name}: Status Code: response.status_code. \n"
            f"Error: {e}"
        )
        return False


# ==========================================
# 2. MAIN SYSTEM ORCHESTRATOR
# ==========================================

"""
ai assistance observed that this section might be better run as a standalone function such as run_pipeline, calling it from the standard configuration below. However, due to time limitations and the ability to pass what is needed to the functions, we left this implementation as is, but are open to modifying it in the future is developers with more experience recommend a change beneficial.
"""

if __name__ == "__main__":
    post_import_dict = {}
    post_verification_dict: dict = {}
    summary_dict: dict = {}

    # Configuration setup environment parsers
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    env.read_env(os.path.join(BASE_DIR, "conf", "wm_api_example.cnf"))

    auth_user = env.str("AUTH_USER")
    auth_passwd = env.str("AUTH_PASSWD")
    debug = env.bool("DEBUG", default=False)
    protocol = env.str("PROTOCOL", default="https")
    port = env.int("PORT", default=5543)
    integration_server = env.str("INTEGRATION_SERVER")
    ssl_certificate_verification = env.bool("VERIFY_SSL_CERTIFICATE", default=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--import_file", nargs="?", const="")
    args = parser.parse_args()

    if not args.import_file:
        print("You did not provide a JSON-formatted import manifest file, exiting.")
        exit(1)

    with open(args.import_file, "r", encoding="utf-8") as f:
        packages_to_import = json.load(f)["wm_import_files"]

    # --- STEP 1: Standalone Server Pre-Flight Check ---
    if not integration_server_status(
        integration_server,
        port,
        auth_user,
        auth_passwd,
        protocol,
        ssl_certificate_verification,
    ):
        print(
            "Aborting webMethods package pipeline import process, integration server health metrics failed.\n"
        )
        exit(1)

    # --- STEP 2: Scoped Loop Execution Management ---
    session = requests.Session()
    session.auth = HTTPBasicAuth(auth_user, auth_passwd)
    session.headers.update({"Accept": "application/json"})

    print(
        f"\nStarting the webMethods package import process consisting of {len(packages_to_import)} packages using "
        f"Python and the wM api ..."
    )
    for zip_file in packages_to_import:
        print(zip_file["name"])
    print()

    try:
        for package in packages_to_import:
            print("-" * 60)

            # Action A: Import the webMethods package
            is_imported, is_imported_package_name, import_text = (
                import_webmethods_package(
                    session, integration_server, port, package, protocol
                )
            )
            print(
                f"Import status: {is_imported}, {is_imported_package_name}, {import_text}\n"
            )
            post_import_dict[is_imported_package_name] = import_text

            # Action B: Execute verification if the import was successful
            if is_imported:
                verification_status, package_name, verification_text = (
                    verify_package_import(
                        session, integration_server, port, package, protocol
                    )
                )
                post_verification_dict[package_name] = verification_text

        print("-" * 60)

        if not post_import_dict:
            print(
                "\nThere were problems with the import process, no import results were returned.\n"
            )

        elif len(post_verification_dict) < len(packages_to_import):
            print(
                "\nThe import process ran to completion, but one or more packages were not verified. Please check the"
                " stdout results and review the following for summary results:\n"
            )

        else:
            print(
                "\nAll pipeline tasks ran to completion. Please review the following for summary results:\n"
            )

        for key, value in post_import_dict.items():
            print(f"{key}: {value}")

        for key, value in post_verification_dict.items():
            print(f"{key}: {value}")
        print()

    finally:
        session.close()

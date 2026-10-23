# wM API Example Project

## Overview

This Python project accesses one or more webMethods (wM) package archive zip files on the host integration server's local file system and imports each file onto the target server. This is an automated method of importing webMethods packages, matching wM Administrator ui functionality. This version should be compatible with recent versions of the standard integration server and the Microservices Runtime (MSR), but only tested using the integration server MSR included in the TechXchange Service Designer version 12 Community release. The script is set up for two inputs, where one is required, a json-formatted list of webMethods zip files.

Most of the detail was found using Google search with ai summarization for help writing a Python process to interact with a webMethods integration server, referencing version 12 integration server documentation where available. We added argparse for processing command-line arguments and environs for following a more standard practice of using a separate file for user accounts and passwords as well as some standard constants like the server name and port. In adding logging, we included the Python [grammlog](https://pypi.org/project/grammlog/) package, which builds upon the standard Python logging module.

We realize this is a minimal ci/cd process just having a Python file that imports packages using the standard wM zip format. Most current wM ci/cd workflows appear to use GitHub for managing the package in the native wM package file system layout, an artifact application like Artifactory, and a ci/cd application like Jenkins. Those processes may also use the wM Deployer application for deployments. The import process was the first version of Deployer, and while Deployer provides much more functionality, it is a licensed product.

Note we are running the integration server included in webMethods Service Designer, so use <service_designer_home> as the base webMethods location. This location differs from the more usual <webmethods_home> identifier for server-based on-premise installations. <project_home> is the directory containing the GitHub project, typically wm_api_example for this project.

The project assumes basic Python experience and little or no webMethods experience.

## Features

- Runs an integration server health check prior to starting the import.
- Reads a json-formatted file containing a list of archive files.
- Imports one or more webMethods package archive zip files onto the target integration server from its local file system, the <service_designer_home>/IntegrationServer/replicate/inbound directory.
- Runs a separate package verification for each import.
- Displays events and summary import results on the command line and logs events to a file.

### Inputs

-i or --import_file \*.json (required), a list of import files, where an example file is located in the GitHub repository at <project_home>/documentation/design/file_formats/wm-import-files-metadata.json.

-l or --log_directory (optional), a log directory location, where if no directory is provided, the process uses the APP_LOG_DIRECTORY value in the <project_home>/src/wm_api_example/conf/wm_api_example.cnf file.

### Output

Informational progress lines printed to stdout and written to the log file. A summary result is also included in stdout.

## About webMethods Integration Server

This project requires a running webMethods integration server. For those who are more Python oriented, Integration Server is part of a larger suite of IBM applications where functionality is now primarily hosted as a cloud offering. Integration Server is available as part of an IBM TechXchange Service Designer Community release as mentioned in the overview. The application has undergone some modernization, marketed as a microservices platform for use in containers.

With that short introduction, running the Python script without connecting to an integration server produces a failed health check error and exits. The integration server installation is documented in more detail for beginners in the next paragraph requiring an IBM login id, a download, and quick installation, then starting the integration server at a minimum.

Another Python/webMethods project goes into further detail of what we just described, plus some tips on using the web-based Administrator application. See [about_webMethods](https://github.com/rrdoue/fastapi_exp/blob/main/z_non-python_resources/webmethods/about_webMethods.md) for suggestions on installing and configuring Integration Server and working with webMethods packages. For the purposes of this project, start near the top of the document and read or execute the following sections:

- Precautionary Note
- Accessing and Downloading webMethods Integration Server
- Service Designer and Integration Server Installation
- Setup and Configuration
- Controlling or Managing Integration Server
- Using Integration Server Administrator and Configuration Suggestions (through Step 5)

Upon completion of all the above sections, go to the end of the about_webmethods readme (just before the references) if one wants to return to the beginning of this readme, or keep both of the readmes open for reference.

Note this import script is an automated version of the about_webMethods section [Manual Package Import Option](https://github.com/rrdoue/fastapi_exp/blob/main/z_non-python_resources/webmethods/about_webMethods.md#manual-package-import-option).

## Python Dependencies

- Python 3.10+ (assumes Python is installed)
- environs
- grammlog (for logging)
- requests (for http calls to the webMethods integration server)
- pytest (not really used)

## webMethods Integration Server Dependencies

- Version 10.15+ due to the health check implementation

## wm_api_example Code Installation

These instructions are provided for setting up the project to run in an IDE or command line terminal using any editor. We'll leave a package on Test PyPI open for consideration. We're attempting to cover both Python and Astral uv virtual environments, since one has been standard for some time and the other is a recent alternative. Note the `$` character is a sample command line prompt. Your prompt in terminal, dos, or PowerShell is probably different.

### git Reference (assumes git is installed)

- In accessing a repository on GitHub, using clone includes the project's git repository, but downloading the zip file does not.
- If one wants to use git to manage file changes, there are a few additional steps after the zip file manual download.
- In either case, add the following lines (or some combination of lines following your accepted practice) to the project's `.gitignore` file to avoid accidentally compromising environment variables in git. We understand the `.cnf` suffix is not standard in Python, but is common in webMethods applications.

\*.cnf  
.env  
\*.env  

### Get the Source

Clone the repository using SSH or download the zip file.

#### Clone the Repository

```bash
# Clone the repository from GitHub
$ cd to/desired/file_system/location
$ git clone git@github.com:rrdoue/wm_api_example.git
$ cd wm_api_example
```

#### Download the Repository Zip File

```bash
# Download the repository file from GitHub using a browser or another method, then unzip the file into the desired directory. Note the download defaults to wm_api_example-main. After unzipping the file, one can rename the resulting directory if you want to copy and paste the instructions here more easily.
$ cd to/desired/file_system/location
$ unzip wm_api_example-main.zip
$ mv wm_api_example-main wm_api_example
$ cd wm_api_example
```

### Set Up a Project Using uv or Python Virtual Environment

- Otherwise one has to add required packages to your default Python installation
- Allows one to remove the installation easily just by deleting the directory

#### uv (assumes uv is installed)

```bash
# run the following in the wm_api_example directory to set up the uv project, which creates a virtual environment and adds dependencies
$ cd to/wm_api_example
$ uv sync
```

#### Python Virtual Environment (available as part of the Python 3 installation)

```bash
# Note one may have to run these as python3 and pip3 in this section
$ cd to/wm_api_example
# create and activate a virtual environment
$ python -m venv .venv
# On Windows, use .venv\Scripts\activate, although PowerShell uses .venv\Scripts\a\Activate.ps1 
$ source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# install the package in development mode, enabling one to use file changes more easily
$ pip install -e .

# The shutdown command for the virtual environment for all OSs and environment managers
$ deactivate
```

#### Add a git Repository When Using a Downloaded Project zip File

```bash
$ cd to/wm_api_example
$ git init
Initialized empty Git repository in /Users/rrdoue/Documents/applications/git/repositories/wm_api_example/.git/
$ git status
On branch main
 ... (the ellipsis indicate you'll see more of a response than included here)
# Now add the entire wm_api_example directory (except for any files listed in the .gitignore file). Note 
$ git add .
$ git commit -m "Initial local wm_api_example commit."
 ...
```

## Usage

One can execute the import script using your favorite command-line terminal or the terminal application in a development environment like PyCharm or VS Code.

### Prerequisites

#### Set Up the Configuration File

Using the sample configuration file in `<project_home>/src/wm_api_example/conf`, set the following values:

- APP_LOG_DIRECTORY
- AUTH_USER
- AUTH_PASSWD
- INTEGRATION_SERVER

then save the file as `wm_api_example.cnf`. As a reminder, the instructions just before this section recommended some entries in the project's `.gitignore` file to avoid versioning the file in source control.

#### Set Up the Processing Files

While this is planned for automation, for now one has to create a file with a list of package archive files to be imported and copy those files to the integration server inbound directory.

##### Control File

Create the json control file required by the import script so the integration server understands the files to process. Use the file <project_home>/documentation/design/file_formats/wm-import-files-metadata.json as an example. For the purpose of trying out this project, one can use the file as is.

#### File Copy

Copy the import archive(s) listed in the control file to the integration server inbound directory

`<service_designer_home>/IntegrationServer/replicate/inbound`

Sample import archives located in the

`<project_home>/documentation/sample/packages`

directory match the sample control file contents mentioned in the previous paragraph. For the purpose of trying out this project, just copy those two zip files to the running integration server's inbound directory.

#### Behavior

If there is an archive file in the control file that isn't in the inbound directory, the script will alert the user, log the problem, and go to the next archive. For the case of an archive file in the located in the inbound directory, but not listed in the control file, the script ignores the archive.

### Running the Process

```bash
$ cd to/wm_api_example
# uv project environment
$ uv run src/wm_api_example/wmapi_import_packages_ai.py -i path/to/wm-import-files-metadata.json

# Python project environment
$ cd to/wm_api_example
$ src/wm_api_example/wmapi_import_packages_ai.py -i path/to/wm-import-files-metadata.json
```

As a note, when executing the import process in a uv-controlled project, one can delete the first line of the Python file, `#! /usr/bin/env python3`, then save and execute the process with the following:

```bash
# uv project environment
$ cd to/wm_api_example
$ src/wm_api_example/wmapi_import_packages_ai.py -i path/to/wm-import-files-metadata.json
```

[Trey Hunner](https://www.pythonmorsels.com/) has more suggestions for making uv-managed project executable files easier to run.

## Return to Other Projects

In case someone visited this readme from the FastAPI sample project, one can return to that project's about_webmethods [readme](https://github.com/rrdoue/fastapi_exp/blob/main/z_non-python_resources/webmethods/about_webMethods.md#sample-package-import-process-option) as desired.

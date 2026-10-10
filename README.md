## Initial Readme File

### Overview

This package accesses one or more webMethods (wM) package archive zip files on the host integration server's local file system, the <webmethods_home>/replicate/inbound directory, and imports each file onto the target server. This is an automated method of importing webMethods packages, matching wM Administrator ui functionality. This version is compatible with the standard integration server and the Microservices Runtime (MSR) version, tested using the integration server included in the version 12 wM Service Designer Community release. The script is set up for two inputs, one required, a json-formatted list of webMethods zip files.

Most of the webMethods detail for the main process was provided using Google search for help writing a Python process to interact with a webMethods integration server, referencing version 12 documentation where available. We added argparse for processing command-line arguments and environs for following a more standard practice of using a separate file for user accounts and passwords as well as some standard constants like the server name, port, and others.

We realize that we're missing lots of ci/cd process just having a basic Python file that imports packages. Most current wM ci/cd workflows use GitHub for managing the entire package in a standard webMethods package file system layout, using an artifact application like Artifactory, and a ci/cd application like Jenkins.

Inputs:

-i (--import_file) \*.json file, example file in the GitHub repository at <project_home>/documentation/design/file_formats/wm-import-files-metadata.json.

-l (--log_directory) Log directory location, where if no directory is provided, the process uses the APP_LOG_DIRECTORY value in the <project_home>/src/wm_api_example/conf/wm_api_example.cnf file.

Output: Informational progress lines printed to stdout and written to the log file. A summary result is also included in stdout.

We realize there is lots of ci/cd process missing just having a basic Python file that imports packages using the standard wM zip format. Most current wM ci/cd workflows use GitHub for managing the entire package in a standard package file system layout, an artifact application like Artifactory, and a ci/cd application like Jenkins. Those processes may also use the wM Deployer application for deployments. The import process was the first version of a deployer and the Deployer application allows for more functionality when migrating wM packages to an integration server.

### About webMethods Integration Server

For those who are more Python oriented, Integration Server is part of a large suite of IBM applications where functionality is now primarily hosted as a cloud offering. Integration Server is a Java application still available for use, probably only by companies who have prior legacy on-premise installations, or by personnel with prior product experience. The application has undergone some modernization, marketed as a microservices platform for use in containers.

Integration Server is typically bundled with an IBM Community edition of webMethods Service Designer, a service and microservice development application for hybrid (on-premise and cloud) integrations. The Community edition is subject to what looks like marketing campaigns, where only the latest version of the product is available. For example, the edition available as of this update is v12.1 r03. This project was executed using v12.1 r01. After registering for an IBM id, one can access the latest download. The jump page follows:

[IBM webMethods Hybrid Integration](https://community.ibm.com/community/user/viewdocument/ibm-webmethods-service-designer-ava?CommunityKey=82b75916-ed06-4a13-8eb6-0190da9f1bfa&tab=librarydocuments)

Where one can find the following download url:

=> [Download IBM webMethods Service Designer](https://www.ibm.com/resources/mrs/assets/DownloadList?source=WMS_Designer_v1213&lang=en_US#lang=en_US)

See [about_webMethods](https://github.com/rrdoue/fastapi_exp/blob/main/z_non-python_resources/webmethods/about_webMethods.md) for suggestions about installing and configuring Integration Server and working with webMethods packages.

### Note for This Project

Add the following lines (or some combination of lines following your accepted practice) to the project's `.gitignore` file to avoid accidentally adding an environment variable file to GitHub. The `.cnf` suffix is not standard in Python, but is common in webMethods applications.

\*.cnf  
.env  
\*.env  

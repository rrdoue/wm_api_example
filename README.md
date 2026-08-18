## Initial Readme File

### Note for This Project

Add the following lines (or some combination of lines following your accepted practice) to the project's .gitignore file to avoid accidentally adding an environment variable file to GitHub. The .cnf suffix is not standard in Python, but is common in webMethods applications.

*.cnf  
.env  
*.env  

### Overview

This package accesses one or more webMethods (wM) package archive zip files on the host integration server's local file system, the <webmethods_home>/replicate/inbound directory, and imports each file onto the target server. This is a more automated method of deploying or importing files, similar to using the wM Administrator ui.

Most of the webMethods api detail for the main process was provided through a Safari Google search for help writing a Python process to interact with a webMethods integration server. We added argparse for some command-line arguments and environs for following a more standard practice of using a separate file for user accounts and passwords as well as some standard constants like the server name, port, and others.

We realize there is lots of ci/cd process missing just having a basic Python file that imports packages using the standard wM zip archive format. Most current wM ci/cd workflows use GitHub for managing the entire package in a standard webMethods formatted package file system layout, using an artifact application like Artifactory, and a ci/cd application like Jenkins. This is more of a sample start on the entire process.

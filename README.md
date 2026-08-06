## Initial Readme File

This accesses one or more webMethods (wM) archive zip files on a local file system where the script runs, although we are more used to deploying files using the wM Administrator ui from the replicate/inbound directory on the host integration server.

Most of the webMethods api detail for the main process was provided through a Safari Google search for help writing a Python process to interact with a webMethods integration server, primarily for this exact process, to import packages following some kind of a more automated process than using the standard wM Administrator ui. We added argparse for some command-line arguments and environs for following a more standard practice of using a separate file for user accounts and passwords as well as some standard constants like the server name, port, and others.

We realize there is lots of ci/cd process missing just having a basic Python file that imports packages using the standard wM zip archive format. Most current wM ci/cd workflows use GitHub for managing the entire package in a standard webMethods formatted package file system layout, using an artifact application like Artifactory, and a ci/cd application like Jenkins.

==========
listpds.py
==========

Take the included **listparms.json** file, read the parameters from it, connect to the specified cluster and list VMs that belong to the specified Protection Domain.

--------------
Important Note
--------------

This script has been written for demo purposes only.  *Please* make sure to add appropriate error-checking and exception handling before using it in production.

------------
Requirements
------------

- Python >=3.6 (lower versions will NOT work)
- pip3 (for dependencies installation)
- Tested on Python 3.6, 3.7 and 3.8

-----
Usage
-----

- Clone repo to your local machine
- Setup a virtual environment on Linux or Mac (strongly recommended):

   .. code-block:: python

      python3.8 -m venv venv
      . venv/bin/activate

- Setup a virtual environment on Windows (strongly recommended):

   .. note:: See https://docs.python.org/3/library/venv.html for Windows instructions

- Install the dependencies:

   .. code-block:: python

      pip3 install -e .

- Run the script:

   .. code-block:: python

      python3.8 listpds.py listparms.json
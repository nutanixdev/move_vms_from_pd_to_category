==========
listpds.py
==========

Take the included **listparms.json** file, read the parameters from it, connect to the specified cluster and list VMs that belong to the specified Protection Domain.

------------
Requirements
------------

- Python >=3.6 (lower versions will NOT work)

-----
Usage
-----

- Clone repo to your local machine
- Setup a virtual environment (stringly recommended):

   .. code-block:: python

      python3.7 -m venv venv
      . venv/bin/activate

- Install the dependencies:

   .. code-block:: python

      pip3 install -e .

- Run the script:

   .. code-block:: python

      python3.7 listpds.py listparms.json
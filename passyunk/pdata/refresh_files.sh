#!/bin/bash

# Author: James Midkiff
set -e
cd /scripts/passyunk/passyunk/pdata
source venv/bin/activate
python refresh_centerline.py 
python format_usps_crlf.py 

deactivate
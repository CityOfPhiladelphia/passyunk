#!/bin/bash

# Author: James Midkiff
set -e
cd /scripts/passyunk/passyunk/pdata
source venv/bin/activate
python refresh_centerline.py 

git add centerline.csv centerline_streets.csv 
git commit -m "Updated centerline" --author="CityGeo_Auto <maps@phila.gov>" # Note that the repository also has the same author and email

deactivate
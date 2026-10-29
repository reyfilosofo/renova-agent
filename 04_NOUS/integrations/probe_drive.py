#!/usr/bin/env python3
"""Authenticated read-only Drive folder smoke test; never prints IDs, names or tokens."""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

token=os.environ.get("NOUS_DRIVE_ACCESS_TOKEN","")
folder=os.environ.get("NOUS_DRIVE_FOLDER_ID","")
if not token or not folder: raise SystemExit("Missing delegated auth or folder configuration")
url="https://www.googleapis.com/drive/v3/files/"+folder+"?"+urlencode({"fields":"mimeType","supportsAllDrives":"true"})
request=Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/json"})
with urlopen(request, timeout=15) as response:
    data=json.loads(response.read(8192))
assert data.get("mimeType")=="application/vnd.google-apps.folder","Configured resource is not a folder"
print("READ_VERIFIED: the scoped Drive folder metadata is accessible. No contents exported.")

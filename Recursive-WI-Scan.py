import requests
import json
import time

# API endpoint and headers
API_ENDPOINT = "http://10.0.1.9:8083/webinspect/api/v1/scanner/scans"
STATUS_ENDPOINT = "http://10.0.1.9:8083/webinspect/api/v1/scanner/scans/{scanId}?action=GetCurrentStatus"
HEADERS = {
    "Content-Type": "application/json",
    # Add any other necessary headers, like authentication headers
}

# Load the base JSON payload
with open("webinspect_payload.json", "r") as f:
    payload_template = json.load(f)

# Read URLs from urls.txt
with open("urls.txt", "r") as f:
    urls = [url.strip() for url in f.readlines()]

# Function to check scan status
def check_scan_status(scan_id, url):
    time.sleep(10)  # Sleeping for 10 seconds to stabilize the status.
    while True:
        response = requests.get(STATUS_ENDPOINT.format(scanId=scan_id), headers=HEADERS)
        if response.status_code == 200:
            status = response.json().get("status")  
            if status == "Complete":
                return True
            elif status in ["Incomplete", "Running", "NotRunning"]:
                print(f"Scan {scan_id} status: {status}.")
                time.sleep(10)  # Wait for 10 seconds before checking again
            elif status in ["Interrupted"]:
                print(f"Scan {scan_id} status: {status}.")
                with open("InterruptedScans.txt", "a+") as Infile:
                    Infile.write(f"The scan for this URL is Interrupted: {url}\n")  
                return True
            else:
                print(f"Unknown status for {scan_id}: {status}")
                return False
        else:
            print(f"Failed to get status for {scan_id}. Response: {response.text}")
            return False

# Start a scan for each URL
for url in urls:
    # Check if the site is reachable
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"{url} is not reachable. Skipping...")
            continue
    except requests.exceptions.RequestException:  # Corrected the exception
        print(f"{url} is not reachable. Skipping...")
        continue
    
    payload = payload_template.copy()
    payload["overrides"]["startUrls"] = [url]
    payload["overrides"]["scanName"] = url
    
    # Send the POST request to start the scan
    response = requests.post(API_ENDPOINT, headers=HEADERS, json=payload)
    
    # Check the response
    if response.status_code == 201:  # Adjusted as per your API response, change if needed
        scan_id = response.json().get("scanId")  # Adjusted the key
        print(f"Scan created successfully for {url} with scanId: {scan_id}")
        if scan_id and not check_scan_status(scan_id, url):  # Passed the url to the function
            print(f"Scan for {url} with scanId {scan_id} did not complete successfully. Stopping further scans.")
            break
    else:
        print(f"Failed to start scan for {url}. Response: {response.text}")

print("All scans initiated.")

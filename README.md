# Deploy a File Scanner for Sensitive Data in 40 Lines of Code

#### In this tutorial, we will create and deploy a server that scans files for sensitive data (like credit card numbers) with Nightfall's data loss prevention APIs and the Flask framework.

The service ingests a local file, scans it for sensitive data with Nightfall, and displays the results in a simple table UI. We'll use tools like Python, Flask, Nightfall, Ngrok, and Render. The end goal is to deploy the server publicly using Render for production, making it accessible beyond your local machine. You may also refer - the file scanner tutorial's GitHub [repo](https://github.com/nightfallai/file-scanner-tutorial).

## Key Concepts

Before we get started on our implementation, start by familiarizing yourself with [how scanning files works](https://docs.nightfall.ai/docs/scanning-files#prerequisites) with Nightfall. Nightfall scans files asynchronously. When a file is uploaded for scanning, Nightfall processes the file in the background and notifies you via a webhook once the scan is complete.

This tutorial builds a client-server architecture:
1. Client: A Python script that triggers a file scan.
2. Server: A Flask app that:
- Handles scan requests from the client.
- Receives webhook notifications from Nightfall with scan results.
- Displays findings in a browser-friendly table.

## Client-Server Architecture
1. Client Script
The client ('client.py') acts as a lightweight interface for triggering file scans. It:
- Sends a POST request to the server's '/scan-request' endpoint, specifying the file to scan.
- Prints the scan ID and confirmation message from the server.

Example Client Code ('client.py')
```python
import requests

server_url = "https://<your-ngrok-url>.ngrok.io/scan-request"  # Replace with your ngrok URL
filepath = "sample-pci-xs.csv"  # The file to scan

response = requests.post(server_url, json={"filepath": filepath})

if response.status_code == 200:
    data = response.json()
    print(f"Scan ID: {data['scan_id']}")
    print(f"Message: {data['message']}")
else:
    print(f"Error: Status Code {response.status_code}")
    print("Response Text:", response.text)

```

2. Server Code
The Flask server ('app.py') manages the following:
- /scan-request: Processes client requests to initiate file scans. It sends the scan request to Nightfall, specifying the '/ingest' webhook URL to receive results.
- /ingest: Receives webhook notifications from Nightfall with scan results. Validates the notification and logs or displays findings.
- /view: Displays findings in a browser-friendly HTML table (optional).

Example Server Code ('app.py')
```python
from flask import Flask, request
import os
from nightfall import Nightfall

app = Flask(__name__)
nightfall = Nightfall(key=os.getenv("NIGHTFALL_API_KEY"), signing_secret=os.getenv("NIGHTFALL_SIGNING_SECRET"))

@app.route("/scan-request", methods=["POST"])
def scan_request():
    data = request.get_json()
    filepath = data.get("filepath")
    webhook_url = f"{os.getenv('NIGHTFALL_SERVER_URL')}/ingest"
    scan_id, message = nightfall.scan_file(filepath, webhook_url=webhook_url)
    return {"scan_id": scan_id, "message": message}, 200

@app.route("/ingest", methods=["POST"])
def ingest():
    data = request.get_json()
    if data.get("challenge"):
        return data["challenge"]
    # Validate webhook, process findings
    return "", 200

```

## How to Run Locally
1. Start the Server
- Run the Flask server locally:
```bash
waitress-serve --port=8000 app:app
```
- Expose the server to the internet using ngrok:
```bash
ngrok http 8000
```
- Set the ngrok HTTPS URL as an environment variable:
```bash
export NIGHTFALL_SERVER_URL=https://<your-ngrok-url>.ngrok.io
```

2. Test the Server
- Run the client script to initiate a scan:
```bash
python client.py
```
- Check the server logs to confirm that the '/ingest' endpoint processes the webhook from Nightfall.

------------------------------------------------------------------------------------------------------

You can fork the sample repo and view the complete code [here](https://github.com/nightfallai/file-scanner-tutorial), or follow along below.

------------------------------------------------------------------------------------------------------

## Setting Up Dependencies

1. Create `requirements.txt` and add the following to the file:

```
nightfall
Flask
Gunicorn
```

2. Install dependencies: `pip install -r requirements.txt` 

## Configuring Nightfall

Retrieve your API Key and Webhook Signing Secret from the Nightfall [Dashboard](https://app.nightfall.ai). Set them as environment variables:

```bash
export NIGHTFALL_API_KEY=<your_key_here>
export NIGHTFALL_SIGNING_SECRET=<your_secret_here>
```

## Handling Webhook Notifications

The '/ingest' route processes webhook notifications sent by Nightfall once the scan is complete. If sensitive findings are detected, it logs the findings and generates a user-friendly URL to display them.

## Scan a File

Create a script 'scan.py' to send files for scanning. It specifies the file path, webhook URL, and the detection rules for Nightfall. 

```python
import os
from nightfall import Confidence, DetectionRule, Detector, Nightfall

nightfall = Nightfall()  # Uses NIGHTFALL_API_KEY by default

filepath = "sample-pci-xs.csv"
webhook_url = f"{os.getenv('NIGHTFALL_SERVER_URL')}/ingest"

scan_id, message = nightfall.scan_file(filepath, 
    webhook_url=webhook_url,
    detection_rules=[
        DetectionRule([
            Detector(
                min_confidence=Confidence.LIKELY,
                nightfall_detector="CREDIT_CARD_NUMBER",
                display_name="Credit Card Number"
            )
        ])
    ]
)

print(scan_id, message)

```
Run 'scan.py' to trigger a file scan.

## Display Results in a Table 

Use the '/view' route to render findings in a table format. Create a folder 'templates/' and add 'view.html' for the HTML layout:

'view.html':

```html
<!DOCTYPE html>
<html>
<head>
    <title>Scan Results</title>
    <style>
        table, th, td { border: 1px solid black; }
        table { width: 100%; }
    </style>
</head>
<body>
    <table>
        <thead>
            <tr>
                <th>Detector</th>
                <th>Finding</th>
                <th>Confidence</th>
            </tr>
        </thead>
        <tbody>
            {% for finding in findings %}
                <tr>
                    <td>{{ finding['detector']['name'] }}</td>
                    <td>{{ finding['finding'] }}</td>
                    <td>{{ finding['confidence'] }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>

```

## Deploy on Render

1. Create a new Web Service on Render.
2. Use the following settings:
- Environment: Python
- Build Command: 'pip install -r requirements.txt'
- Start Command: 'gunicorn app:app'
3. Add environment variabls:
```bash
NIGHTFALL_API_KEY=<your_api_key>
NIGHTFALL_SIGNING_SECRET=<your_signing_secret>
```

## Test the Deployed Server

1. Update the 'NIGHTFALL_SERVER_URL' to the Render app URL.
2. Run 'scan.py' to trigger file scans through the deployed server.

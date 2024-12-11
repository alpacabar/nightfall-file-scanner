import os
from flask import Flask, request, render_template
from nightfall import Confidence, DetectionRule, Detector, RedactionConfig, MaskConfig, Nightfall
from datetime import datetime, timedelta
import urllib.request, urllib.parse, json

app = Flask(__name__)

nightfall = Nightfall(
	key=os.getenv('NIGHTFALL_API_KEY'),
	signing_secret=os.getenv('NIGHTFALL_SIGNING_SECRET')
)

@app.route("/")
def ping():
	return "Hello World", 200

@app.route("/ingest", methods=['POST'])
def ingest():
    data = request.get_json(silent=True)
    print("Received Data:", data)  # Debugging print for data

    # validate webhook URL with challenge response
    challenge = data.get("challenge") 
    if challenge:
        print("Challenge received:", challenge)
        return challenge

    # get details of the inbound webhook request for validation
    request_signature = request.headers.get('X-Nightfall-Signature')
    request_timestamp = request.headers.get('X-Nightfall-Timestamp')
    request_data = request.get_data(as_text=True)

    # Debugging prints for headers and raw request data
    print("Request Signature:", request_signature)
    print("Request Timestamp:", request_timestamp)
    print("Request Data:", request_data)

    # Validate webhook if data is present
    if nightfall.validate_webhook(request_signature, request_timestamp, request_data):
        # check if any sensitive findings were found in the file
        if not data.get("findingsPresent"): 
            print("No sensitive data present!")
            return "", 200

        # Process findings if present
        escaped_url = urllib.parse.quote(data['findingsURL'])
        print(f"Sensitive data present. Findings available until {data['validUntil']}.\n\nDownload:\n{data['findingsURL']}\n\nView:\n{request.url_root}view?findings_url={escaped_url}\n")
        return "", 200
    else:
        print("Invalid webhook signature or timestamp.")
        return "Invalid webhook", 500


# respond to GET requests at /view
# Users can access this page to view their file scan results in a table
@app.route("/view")
def view():
	# get the findings URL from the query parameters
	findings_url = request.args.get('findings_url')
	if findings_url:
		# download the findings from the findings URL and parse them as JSON
		with urllib.request.urlopen(findings_url) as url:
			data = json.loads(url.read().decode())
			# render the view.html template and provide the findings object to display in the template
			return render_template('view.html', findings=data['findings'])

@app.route("/scan-request", methods=['POST'])
def scan_request():
    data = request.get_json()
    filepath = data.get("filepath")  # Expecting the client to send a file path
    webhook_url = f"{os.getenv('NIGHTFALL_SERVER_URL')}/ingest"

    if not filepath:
        return {"error": "File path is required"}, 400

    # Initiate file scan
    scan_id, message = nightfall.scan_file(
        filepath, 
        webhook_url=webhook_url,
        detection_rules=[DetectionRule([
            Detector(
                min_confidence=Confidence.LIKELY,
                nightfall_detector="CREDIT_CARD_NUMBER",
                display_name="Credit Card Number"
            )])
        ]
    )
    return {"scan_id": scan_id, "message": message}, 200

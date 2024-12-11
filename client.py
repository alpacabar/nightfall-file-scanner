import requests

server_url = "https://e021-164-125-221-121.ngrok-free.app/scan-request"  # Use the ngrok URL
filepath = "sample-pci-xs.csv"  # Path to the file you want to scan

response = requests.post(server_url, json={"filepath": filepath})

if response.status_code == 200:
    data = response.json()
    print(f"Scan ID: {data['scan_id']}")
    print(f"Message: {data['message']}")
else:
    print(f"Error: Status Code {response.status_code}")
    print("Response Text:", response.text)


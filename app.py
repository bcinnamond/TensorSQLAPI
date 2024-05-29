from flask import Flask, requests, jsonify
import pymysql
import datetime
from datetime import date
from requests_oauthlib from OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient

app = Flask(__name__)

# Database connection parameters
server = 'XXXXX'
database = 'XXXXX'
username = 'XXXXX'
password = 'XXXXX'

# Syteline API connection parameters
styline_endpoint = 'YOUR_ENDPOINT'
client_id = ionapi["ci"]
tenantid = ionapi["ti"]
client_secret = ionapi["cs"]
username = ionapi["saak"]
password = ionapi["sask"]
ionapiTokenURL = ionapi["pu"]+ionapi["ot"]
mongoose_config = "YOUR_MONGOOSE_CONFIG"

# Database query method 
def query_database(query):
    conn = pymysql.connect(server, username, password, database)
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()
    return result

# Method to fetch access token from Infor ION
def get_access_token():
    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=client_id))
    token = oauth.fetch_token(token_url=ionapiTokenURL,
        username=username, password=password, client_id=client_id,
        client_secret=client_secret)
    print("token retrieved using : " + ionapiTokenURL)
    
# Method to format and send JSON to Syteline endpoint
def send_data_to_syteline_api(employee_hours, access_token):
    changes = []
    for entry in employee_hours:
        change = {
            "Action": 1,
            "ItemId": "PBT=[ue_EmployeeEfficiency]",
            "Properties": [
                {
                    "Name": "employee_code",
                    "Value": entry['employee_code'],
                    "Modified": True,
                    "IsNull": False
                },
                {
                    "Name": "day_summary_header_id",
                    "Value": str(entry['day_summary_header_id']),
                    "Modified": True,
                    "IsNull": False
                },
                {
                    "Name": "total_hours",
                    "Value": str(entry['total_hours']),
                    "Modified": True,
                    "IsNull": False
                },
                {
                    "Name": "date",
                    "Value": entry['date'],
                    "Modified": True,
                    "IsNull": False
                }
            ],
            "UpdateLocking": 1
        }
        changes.append(change)

    payload = {"Changes": changes}

    headers = {
        'Authorization': f'Bearer {access_token}',
        "X-Infor-MongooseConfig": mongoose_config,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(styline_endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Syteline API: {e}")
        return []

# get_employee_hours method and endpoint route
@app.route('/get_employee_hours', methods=['GET'])
def get_employee_hours():
    # Get today's date
    today_date = datetime.date.today()

    # Query to get DayID and EmployeeID
    header_query = f"SELECT DayID, EmployeeID FROM DayHeader WHERE ProcessingDate = '{today_date}'"
    header_results = query_database(header_query)

    employee_hours = []

    # Iterate through each DaySummaryHeaderID
    for header in header_results:
        day_id = header[0]
        employee_id = header[1]

        #Query Employees for EmployeeCode 
        employee_code_query= f"SELECT EmployeeCode From Employee WHERE EmployeeID = {employee_id}"
        employee_code_result = query_database(employee_code_query)

        if employee_code_result:
            employee_code = employee_code_result[0][0]
        else:
            employee_code = None

        # Query to get DayDetailID, FromDateTime, and ToDateTime
        detail_query = f"SELECT DayDetailID, FromDateTime, ToDateTime FROM DayDetail WHERE DayID = {day_id}"
        detail_results = query_database(detail_query)

        # Calculate total hours
        total_hours = 0
        for detail in detail_results:
            from_datetime = detail[1]
            to_datetime = detail[2]

            if to_datetime is not None:
                hours_difference = (to_datetime - from_datetime).total_seconds() / 3600
                total_hours += hours_difference


    # Commented out this method as the Syteline endpoint is unavailable
    # response = send_data_to_syteline_api(employee_hours)

    #return the data as an output instead. 
    return jsonify(employee_hours)


if __name__ == '__main__':
    app.run()

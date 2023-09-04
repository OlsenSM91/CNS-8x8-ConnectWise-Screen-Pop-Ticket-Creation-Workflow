from flask import Flask, request, render_template
import requests
import base64
from decouple import config

app = Flask(__name__)

# Load secrets from .env
CLIENT_ID = config('CLIENT_ID')
PUBLIC_API_KEY = config('PUBLIC_API_KEY')
PRIVATE_API_KEY = config('PRIVATE_API_KEY')
COMPANY_ID = config('COMPANY_ID')

BASE_URL = "https://services.cns4u.com/v4_6_release/apis/3.0"

# Create the base64 encoded header for authentication
auth_string = f"{COMPANY_ID}+{PUBLIC_API_KEY}:{PRIVATE_API_KEY}"
encoded_auth_string = base64.b64encode(auth_string.encode()).decode()

# Define headers for API requests
HEADERS = {
    'Authorization': f"Basic {encoded_auth_string}",
    'clientId': CLIENT_ID
}

@app.route('/')
def index():
    """Root endpoint that welcomes the user."""
    return "Welcome to the ConnectWise Integration App!"

@app.route('/phone')
def phone():
    phone_number = request.args.get('phone')
    # Use the direct endpoint to search by phone number
    response = requests.get(f"{BASE_URL}/company/companies?conditions=phoneNumber%20like%20'{phone_number}'", headers=HEADERS)
    
    if response.status_code == 200:
        try:
            companies = response.json()
            if companies:
                company_id = companies[0]['id']
                contacts_response = requests.get(f"{BASE_URL}/company/companies/{company_id}/contacts", headers=HEADERS)
                contacts = contacts_response.json() if contacts_response.status_code == 200 else []
                return render_template('company.html', company=companies[0], contacts=contacts)
            else:
                return "No company found with the provided phone number.", 404
        except requests.exceptions.JSONDecodeError:
            return f"Error decoding JSON: {response.text}", 500
    else:
        # Return the detailed error message from the API
        return f"API returned status code {response.status_code}: {response.json().get('message', response.text)}", 500

@app.route('/create-ticket', methods=['POST'])
def create_ticket():
    title = request.form.get('title')
    description = request.form.get('description')
    company_id = request.form.get('company_id')
    
    data = {
        "company": {"id": company_id},
        "summary": title,  # Using "Summary" for the ticket title
        "initialDescription": description,  # Using "Initial Description" for the ticket description
        "board": {"name": "RX Automate"},
        "status": {"name": "New (portal)"}
    }

    response = requests.post(f"{BASE_URL}/service/tickets", headers=HEADERS, json=data)
    
    if response.status_code == 201:
        return "Ticket created successfully!"
    else:
        error_message = response.json().get('message', response.text)
        error_details = response.json().get('errors', [])
        detailed_error = '; '.join([error.get('message', '') for error in error_details])
        return f"Failed to create ticket. Error: {error_message}. Details: {detailed_error}", 400

if __name__ == '__main__':
    app.run(debug=True, port=6969)

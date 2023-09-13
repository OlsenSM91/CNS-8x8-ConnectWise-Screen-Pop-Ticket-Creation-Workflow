from flask import Flask, request, render_template
import requests
import base64
from decouple import config
import logging

logging.basicConfig(level=logging.DEBUG)

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

def fetch_all_contacts_for_company(company_id):
    """Fetch all contacts associated with a given company ID."""
    contacts = []
    page_number = 1

    while True:
        response = requests.get(f"{BASE_URL}/company/companies/{company_id}/contacts?pageSize=1000&page={page_number}", headers=HEADERS)
        
        if response.status_code != 200:
            logging.error(f"Error fetching contacts for company ID {company_id} on page {page_number}. Status code: {response.status_code}")
            break

        company_contacts = response.json()
        if not company_contacts:
            break

        contacts.extend(company_contacts)
        page_number += 1

    return contacts

@app.route('/')
def index():
    """Root endpoint that welcomes the user."""
    return "Welcome to the ConnectWise Integration App!"

@app.route('/phone')
def phone():
    phone_number = request.args.get('phone')
    phone_number = ''.join(filter(str.isdigit, phone_number))
    contacts = []
    page_number = 1
    matched_contact = None

    # Step 1: Search by Individual's Phone Number
    while True:
        contacts_response = requests.get(f"{BASE_URL}/company/contacts?pageSize=1000&page={page_number}", headers=HEADERS)
        if contacts_response.status_code != 200:
            logging.error(f"Error fetching contacts for page {page_number}. Status code: {contacts_response.status_code}")
            break
        
        contacts = contacts_response.json()
        if not contacts:
            break

        matched_contact = next((contact for contact in contacts if contact.get('defaultPhoneNbr') == phone_number), None)
        if matched_contact:
            matched_company_id = matched_contact['company']['id']
            company_response = requests.get(f"{BASE_URL}/company/companies/{matched_company_id}", headers=HEADERS)
            if company_response.status_code == 200:
                matched_company = company_response.json()
                company_contacts = [contact for contact in contacts if 'company' in contact and contact['company'].get('id') == matched_company['id']]
                return render_template('company.html', company=matched_company, contacts=company_contacts, matched_contact=matched_contact)

        page_number += 1

    # Step 2: Search by Company's Primary Phone Number
    company_search_response = requests.get(f"{BASE_URL}/company/companies?conditions=phoneNumber='{phone_number}'", headers=HEADERS)
    
    if company_search_response.status_code == 200 and company_search_response.json():
        matched_company = company_search_response.json()[0]  # Take the first matched company
        company_contacts = fetch_all_contacts_for_company(matched_company['id'])
        return render_template('company.html', company=matched_company, contacts=company_contacts, matched_contact=None)

    return "No individual or company found with the provided phone number.", 404

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

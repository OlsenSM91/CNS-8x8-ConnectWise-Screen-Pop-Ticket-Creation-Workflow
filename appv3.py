from flask import Flask, request, render_template, redirect, jsonify
import requests
import base64
from decouple import config
import logging
from datetime import datetime

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
    company_name = request.args.get('companyName')

    if company_name:
        # Search by Company Name
        company_search_response = requests.get(f"{BASE_URL}/company/companies?conditions=name like '%{company_name}%'", headers=HEADERS)
        
        if company_search_response.status_code == 200 and company_search_response.json():
            matched_company = company_search_response.json()[0]  # Take the first matched company
            company_contacts = fetch_all_contacts_for_company(matched_company['id'])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return render_template('company.html', company=matched_company, contacts=company_contacts, matched_contact=None, timestamp=timestamp)
        
        else:
            return "No company found with the provided name.", 404

    elif phone_number:
        # Normalize phone number
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
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    return render_template('company.html', company=matched_company, contacts=company_contacts, matched_contact=matched_contact, timestamp=timestamp)

            page_number += 1

        # Step 2: Search by Company's Primary Phone Number
        company_search_response = requests.get(f"{BASE_URL}/company/companies?conditions=phoneNumber='{phone_number}'", headers=HEADERS)
        
        if company_search_response.status_code == 200 and company_search_response.json():
            matched_company = company_search_response.json()[0]  # Take the first matched company
            company_contacts = fetch_all_contacts_for_company(matched_company['id'])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return render_template('company.html', company=matched_company, contacts=company_contacts, matched_contact=None, timestamp=timestamp)

        return redirect('/add-contact')

    else:
        return "Please provide a phone number or company name.", 400
        
@app.route('/add-contact')
def add_contact():
    return render_template('add_contact.html')

@app.route('/create-ticket', methods=['POST'])
def create_ticket():
    title = request.form.get('title')
    description = request.form.get('description')
    company_id = request.form.get('company_id')
    
    # Get Board and Status from form data
    board_name = request.form.get('board')
    status_name = request.form.get('status')

    # Construct the ticket payload
    data = {
        "company": {"id": company_id},
        "summary": title,  # Using "Summary" for the ticket title
        "initialDescription": description,  # Using "Initial Description" for the ticket description
        "board": {"name": board_name},
        "status": {"name": status_name}
    }

    response = requests.post(f"{BASE_URL}/service/tickets", headers=HEADERS, json=data)
    
    if response.status_code == 201:
        return "Ticket created successfully!"
    else:
        error_message = response.json().get('message', response.text)
        error_details = response.json().get('errors', [])
        detailed_error = '; '.join([error.get('message', '') for error in error_details])
        return f"Failed to create ticket. Error: {error_message}. Details: {detailed_error}", 400

@app.route('/search-companies')
def search_companies():
    """Search for companies based on a query."""
    query = request.args.get('query')
    if not query:
        return jsonify([])

    # Search companies based on the query
    company_search_response = requests.get(f"{BASE_URL}/company/companies?conditions=name like '%{query}%'", headers=HEADERS)
    
    if company_search_response.status_code == 200:
        return jsonify(company_search_response.json())
    else:
        return jsonify([])

@app.route('/add-contact-to-existing', methods=['POST'])
def add_contact_to_existing():
    """Add a contact to an existing company."""
    # Extract form data
    company_id = request.form.get('companyId')
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    phone = request.form.get('phone')

    # Prepare data for API request
    contact_data = {
            "firstName": first_name,
            "lastName": last_name,
            "company": {"id": company_id},
            "defaultPhoneType": "Mobile",
            "defaultPhoneNbr": phone,
            "communicationItems": [
                {
                    "type": {"id": 1, "name": "Email"},
                    "value": email,
                    "defaultFlag": False,  # Ensure defaultFlag is set to False for email
                    "communicationType": "Email"
                },
                {
                    "type": {"id": 4, "name": "Mobile"},
                    "value": phone,
                    "defaultFlag": True,  # Ensure defaultFlag is set to True for mobile
                    "communicationType": "Phone"
                }
            ]
        }

    # Send API request to add the contact
    response = requests.post(f"{BASE_URL}/company/contacts", json=contact_data, headers=HEADERS)
    
    if response.status_code == 201:
        # Redirect to the /phone route with the newly created contact details
        return redirect(f"/phone?phone={phone}")
    else:
        # Handle errors (for simplicity, just returning the error message here)
        return response.text


@app.route('/create-company-and-contact', methods=['POST'])
def create_company_and_contact():
    """Create a new company and add a contact to it."""
    # Extract form data for company
    company_name = request.form.get('companyName')
    site = request.form.get('site')
    address = request.form.get('address')
    company_phone = request.form.get('companyPhone')
    company_id = request.form.get('companyId')

    # Extract form data for contact
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    phone = request.form.get('phone')

    # Prepare data for API request to create company
    company_data = {
        "name": company_name,
        "site": site,
        "address": address,
        "phone": company_phone,
        "id": company_id
    }

    # Send API request to create the company
    company_response = requests.post(f"{BASE_URL}/company/companies", json=company_data, headers=HEADERS)
    
    if company_response.status_code == 201:
        created_company = company_response.json()
        # Prepare data for API request to add contact to the newly created company
        contact_data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "company": {
                "id": created_company['id']
            }
        }
        # Send API request to add the contact
        contact_response = requests.post(f"{BASE_URL}/company/contacts", json=contact_data, headers=HEADERS)
        if contact_response.status_code == 201:
            # Redirect to the /phone route with the newly created contact details
            return redirect(f"/phone?phone={phone}")
        else:
            # Handle errors (for simplicity, just returning the error message here)
            return contact_response.text
    else:
        # Handle errors (for simplicity, just returning the error message here)
        return company_response.text
        
@app.route('/contact-details/<int:contact_id>')
def get_contact_details(contact_id):
    """Retrieve full details about a contact by their ID."""
    
    # Send API request to fetch the contact details
    response = requests.get(f"{BASE_URL}/company/contacts/{contact_id}", headers=HEADERS)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return f"Failed to retrieve contact details. Error: {response.text}", 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=6699)

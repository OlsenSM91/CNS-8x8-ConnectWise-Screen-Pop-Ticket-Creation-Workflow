from flask import Flask, request, render_template, redirect, jsonify
import requests
import base64
from decouple import config
import logging
from datetime import datetime, timezone
import dateutil.parser

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
    
def generate_company_identifier(company_name, max_length=30):
    # Remove non-alphanumeric characters and replace spaces with a single space
    identifier = ''.join(e for e in company_name if e.isalnum() or e == ' ')
    identifier = ' '.join(identifier.split())

    # Trim to the maximum length
    identifier = identifier[:max_length]

    # Ensure the last character isn't a space
    return identifier.rstrip()
    
def create_identifier_from_company_name(company_name):
    identifier = company_name[:23]  # get the first 23 characters
    identifier = ''.join(e for e in identifier if e.isalnum())  # strip out non-alphanumeric characters
    return identifier
    
def fetch_open_tickets(page_number=1, page_size=100):
    """Fetch a specific set of open tickets based on pagination, excluding tickets assigned to 'CHolt'."""
    tickets = []

    # Conditions to exclude certain statuses
    conditions = (
        "status/name!='>cancelled' AND "
        "status/name!='>closed' AND "
        "status/name!='Closed' AND "
        "status/name!='Ready to Bill'"
    )

    # Construct the URL with pagination and conditions
    url = f"{BASE_URL}/service/tickets?conditions={conditions}&orderBy=dateEntered asc&pageSize={page_size}&page={page_number}"
    response = requests.get(url, headers=HEADERS)

    logging.info(f"Requesting URL: {url}")
    if response.status_code != 200:
        logging.error(f"Error fetching tickets for page {page_number}. Status code: {response.status_code}")
        return []

    all_tickets = response.json()

    # Filter out tickets where the assigned technician is 'CHolt'
    # Assuming that the technician's name is stored in a field that can be accessed appropriately
    tickets = [ticket for ticket in all_tickets if 'CHolt' not in ticket.get('resources', '')]

    return tickets
    
def calculate_age(date_entered_str):
    date_entered = datetime.fromisoformat(date_entered_str.replace("Z", "+00:00"))
    current_date = datetime.now(timezone.utc)
    age = (current_date - date_entered).days
    return age

def fetch_open_tickets_for_dashboard(page_number=1, page_size=100):
    """Fetch tickets for the dashboard with pagination, accounting for post-fetch filtering."""
    all_tickets = []
    current_api_page = 1

    while len(all_tickets) < page_size * page_number:
        fetched_tickets = fetch_tickets_from_api(page_number=current_api_page, page_size=100)
        current_api_page += 1

        for ticket in fetched_tickets:
            if 'CHolt' not in ticket.get('resources', ''):
                ticket_age = calculate_age(ticket['_info']['dateEntered'])
                ticket['age'] = ticket_age
                all_tickets.append(ticket)

        if len(fetched_tickets) < 100:
            break

    start_index = (page_number - 1) * page_size
    return all_tickets[start_index:start_index + page_size]

def fetch_tickets_from_api(page_number, page_size):
    """Fetch a set of tickets from the API."""
    conditions = (
        "status/name!='>cancelled' AND "
        "status/name!='>closed' AND "
        "status/name!='Closed' AND "
        "status/name!='Ready to Bill'"
    )
    url = f"{BASE_URL}/service/tickets?conditions={conditions}&orderBy=dateEntered asc&pageSize={page_size}&page={page_number}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        logging.error(f"Error fetching tickets from API. Status code: {response.status_code}")
        return []

    return response.json()

@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    tickets_per_page = 100  # Number of tickets to display per page
    tickets = fetch_open_tickets_for_dashboard(page_number=page, page_size=tickets_per_page)

    # Generate the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Estimate the total number of pages (update this logic as needed)
    total_tickets_estimate = 200  # Example estimate
    total_pages = (total_tickets_estimate + tickets_per_page - 1) // tickets_per_page

    return render_template('dashboard.html', tickets=tickets, current_page=page, total_pages=total_pages, timestamp=timestamp)

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
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('add_contact.html', timestamp=timestamp)

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

@app.route('/project/tickets/<int:ticket_id>/notes', methods=['GET'])
def get_ticket_notes(ticket_id):
    """Fetch notes for a specific ticket."""
    response = requests.get(f"{BASE_URL}/service/tickets/{ticket_id}/notes", headers=HEADERS)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to fetch ticket notes'}), response.status_code

@app.route('/project/tickets/<int:ticket_id>/notes', methods=['POST'])
def add_ticket_note(ticket_id):
    """Add a new note to a specific ticket."""
    data = request.json
    note_data = {
        "text": data['text'],
        "detailDescriptionFlag": data['detailDescriptionFlag'],
        "internalAnalysisFlag": data['internalAnalysisFlag'],
        "resolutionFlag": data['resolutionFlag']
    }

    response = requests.post(f"{BASE_URL}/service/tickets/{ticket_id}/notes", headers=HEADERS, json=note_data)
    if response.status_code == 201:
        return jsonify({'message': 'Note added successfully'}), 201
    else:
        return jsonify({'error': 'Failed to add note'}), response.status_code

@app.route('/project/boards/<int:board_id>/statuses', methods=['GET'])
def get_board_statuses(board_id):
    """Fetch available statuses for a specific board."""
    response = requests.get(f"{BASE_URL}/service/boards/{board_id}/statuses", headers=HEADERS)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to fetch statuses'}), response.status_code

@app.route('/service/boards', methods=['GET'])
def get_service_boards():
    """Fetch all available service boards."""
    response = requests.get(f"{BASE_URL}/service/boards", headers=HEADERS)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to fetch boards'}), response.status_code
        
@app.route('/project/tickets/<int:ticket_id>/status', methods=['POST'])
def update_ticket_status(ticket_id):
    """Update the status of a specific ticket."""
    data = request.json  # Get the new status ID from the request body
    new_status_id = data.get('status')

    if not new_status_id:
        return jsonify({'error': 'Status ID is required'}), 400

    # Fetch the existing ticket to get its current details
    response = requests.get(f"{BASE_URL}/service/tickets/{ticket_id}", headers=HEADERS)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch existing ticket details'}), response.status_code

    ticket = response.json()

    # Update the ticket object with the new status
    ticket['status'] = {'id': new_status_id}

    # Ensure all required fields are present (these should already be part of the existing ticket)
    required_fields = ['summary', 'board', 'company', 'priority', 'severity', 'impact']
    for field in required_fields:
        if field not in ticket or not ticket[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Send the updated ticket back to the API
    update_response = requests.put(f"{BASE_URL}/service/tickets/{ticket_id}", headers=HEADERS, json=ticket)
    if update_response.status_code == 200:
        return jsonify({'message': 'Status updated successfully'}), 200
    else:
        logging.error(f"Failed to update status for ticket {ticket_id}. Status code: {update_response.status_code}, Response: {update_response.text}")
        return jsonify({'error': 'Failed to update status', 'details': update_response.text}), update_response.status_code

@app.route('/create-company-and-contact', methods=['POST'])
def create_company_and_contact():
    """Create a new company and add a contact to it."""
    # Extract form data for company
    company_name = request.form.get('companyName')
    address = request.form.get('address')
    company_phone = request.form.get('companyPhone')
    territory = request.form.get('territory')
    city = request.form.get('city')
    state = request.form.get('state')
    zip_code = request.form.get('zip')

    # Extract form data for contact
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    # Generate Company Identifier to Satisfy API POST requirements
    company_identifier = generate_company_identifier(company_name)

    # Prepare data for API request to create company
    company_data = {
        "identifier": company_identifier,
        "name": company_name,
        "addressLine1": address,
        "addressLine2": f"{city}, {state} {zip_code}",
        "phoneNumber": company_phone,
        "territory": {"name": territory},
        "site": {"name": "Main Office"}
    }

    # Send API request to create the company
    company_response = requests.post(f"{BASE_URL}/company/companies", json=company_data, headers=HEADERS)
    
    if company_response.status_code == 201:
        created_company = company_response.json()
        # Prepare data for API request to add contact to the newly created company
        contact_data = {
            "firstName": first_name,
            "lastName": last_name,
            "defaultPhoneType": "Mobile",
            "defaultPhoneNbr": phone,
            "company": {"id": created_company['id']},
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
        contact_response = requests.post(f"{BASE_URL}/company/contacts", json=contact_data, headers=HEADERS)
        # After creating the contact:
        if contact_response.status_code == 201:
            created_contact = contact_response.json()
            contact_id = created_contact['id']

        # Update the company with the new primary contact
        company_update_data = {
            "identifier": created_company['identifier'],
            "name": created_company['name'],
            "status": {"name": "Not-Approved"},
            "defaultContact": {"id": contact_id},
            "billToCompany": {"id": created_company['id']},
            "addressLine1": created_company['addressLine1'],
            "addressLine2": created_company['addressLine2'],
            "phoneNumber": created_company['phoneNumber']
        }

        company_update_response = requests.put(f"{BASE_URL}/company/companies/{created_company['id']}", json=company_update_data, headers=HEADERS)

        if company_update_response.status_code != 200:
            # Handle errors (for simplicity, just returning the error message here)
            return f"Failed to update the company's primary contact. Error: {company_update_response.text}", 400

        else:
            # Continue to phone route with new contact information
            return redirect(f"/phone?phone={phone}")
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
    app.run(host='0.0.0.0', debug=True, port=6969)

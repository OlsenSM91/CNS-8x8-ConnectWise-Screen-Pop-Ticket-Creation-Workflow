# ConnectWise 8x8 Screen Pop Integration Application

![screenpop](https://github.com/OlsenSM91/CW8x8ScreenPop/assets/130707762/6c489673-1c0b-46b5-9dd9-fd6fa52c4595)

This integration Screen Pop is designed to seamlessly connect with the ConnectWise API using the 8x8 Caller ID screen pop setting, allowing users to search for client details using a phone number and create tickets directly from the interface.

## Features

- **Screen Pop**: Use a URL such as `http://localhost:6969/phone?phone=%%PhoneNUmber%%` with Screen Pop Caller ID from 8x8 Work applications
- **Client Search**: Quickly search for client details using a phone number.
- **Detailed Client Information**: View essential client details such as company name, contact information, address, and more.
- **Ticket Creation**: Easily create tickets with a summary and description for the searched client.

## How It Works

1. **Client Search**: The main interface provides a search box where users can input a phone number. Upon submission, the app queries the ConnectWise API to fetch details associated with the provided phone number.
2. **Display Client Details**: Once the client details are fetched, they are displayed in a structured format. This includes company details, contact information, and address.
3. **Ticket Creation**: Below the client details, there's an option to create a ticket. Users can input a summary and description and submit. The ticket gets created in ConnectWise for the respective client.

## Usage

1. **Clone the Repository**: Start by cloning this repository to your local machine.
2. **Setup Environment Variables**: Ensure you have a `.env` file in the root directory with the necessary API keys and credentials.
3. **Install Dependencies**: Use `pip install -r requirements.txt` to install the necessary Python packages.
4. **Run the App**: Start the Flask app using `flask run` or `python app.py`.
5. **Access the Interface**: Open a web browser and navigate to `http://localhost:5000` (or the port you've specified).
6. **Search by Phone Number**: On the main interface, input a phone number into the search box and click "Search". The app will display client details associated with the phone number. From there, you can also create a ticket for the client.

## Author

Made with ❤️ by Steven Olsen

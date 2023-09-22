# CNSRx 8x8 ScreenPop ConnectWise Integration

If you're an MSP that uses ConnectWise Manage/PSA as well as 8x8 VoIP phone systems, this integration app will utilize a ConnectWise Manage API to perform a screen pop via the "Caller Info Pop Up" settings within the 8x8 Work Application.

This particular complete working code is themed for our company, but a bit of CSS and rebranding for your company and you too can not spend hours coding and looking through the ConnectWise API documentation to get a screen pop for your business.

![screenpop](https://github.com/OlsenSM91/CNS-8x8-ConnectWise-Screen-Pop-Ticket-Creation-Workflow/assets/130707762/6abf1a37-da46-409e-9bd1-31d7bb0fc94a)

This integration Screen Pop is designed to seamlessly connect with the ConnectWise API using the 8x8 Caller ID screen pop setting, allowing users to search for client details using a phone number and create tickets directly from the interface.

## Features

- **Screen Pop**: Use a URL such as `http://localhost:6969/phone?phone=%%CallerNumber%%` with Screen Pop Caller ID from 8x8 Work applications. Ensure you set the 8x8 number to be the national number with no 1 before the area code so it's like `5555555555`.
- **Client Search**: Quickly search for client details using a phone number.
- **Detailed Client Information**: View essential client details such as company name, contact information, address, and more.
- **Ticket Creation**: Easily create tickets with a summary and description for the searched client.
- **Add New Contact**: If the phone number isn't found, you have the ability to add a new contact to the system.
- **Company Search**: If a company doesn't exist, search for existing companies to add the contact to.

## How It Works

1. **Client Search**: The main function of this application is to be utilized via the `/phone` route as a call comes in which will search the contact lists, on the client details page, it provides a search box where users can input a phone number or company name to search. Upon submission, the app queries the ConnectWise API to fetch details associated with the provided phone number.
2. **Display Client Details**: Once the client details are fetched, they are displayed in a structured format. This includes company details, contact information, and address.
3. **Ticket Creation**: Below the client details, there's an option to create a ticket. Users can input a summary and description and submit. The ticket gets created in ConnectWise for the respective client.
4. **Add New Contact**: If the search doesn't return any results, the option to add a new contact is provided. You can also associate the contact with an existing company or add a new company if needed.

## Configuration

Rename the `.envtemplate` file to `.env` and update it with the necessary API keys and credentials.
- `CLIENT_ID`: ConnectWise client ID
- `PUBLIC_API_KEY`: Public API key for ConnectWise
- `PRIVATE_API_KEY`: Private API key for ConnectWise
- `COMPANY_ID`: Company ID for ConnectWise

Additionally, if you intend to use this for your company, you will need to modify the html files in the `/templates/` directory to be branded for your company

Also the port set at the bottom line of app.py can be changed to suit your environment. It is also binded to all network devices, so it can be accessed by other devices on the network. The `host='0.0.0.0'` can be removed to bind to localhost only. This application is **NOT** intended to be exposed to the open internet as this is not a production level application. I repeat **DO NOT** expose this to the world wide web. If you are insistent **DO NOT** expose ports, instead use a reverse proxy or zero trust tunnel. Again, it is not recommended as anyone would be able to access your client data without needing to authenticate

## Usage

1. **Clone the Repository**: Start by cloning/downloading this repository to your local machine.
2. **Setup Environment Variables**: Copy the `.envtemplate` file to a `.env` and update it with the necessary API keys and credentials.
3. **Setup Base URL**: The BASE_URL variable is the base URL for your companies CW Manage/PSA server. Please note that if using the hosted CW PSA, you can obtain the Base URLs from `https://developer.connectwise.com` if you are self hosted, you can follow the Base URL that's currently being set within `app.py` to match your access URL.
3. **Install Dependencies**: Use `pip install -r requirements.txt` to install the necessary Python packages.
4. **Run the App**: Start the Flask app using `flask run` or `python app.py`.
5. **Access the Interface**: Open a web browser and navigate to `http://localhost:6969` (or the port you've specified). This will pop up with a message that the application is running
6. **Configure the ScreenPop**: Within the 8x8 Work Application, click on the `Settings` gear icon and choose `Caller info pop-up` option and enter in the URL like:
`http://localhost:6969/phone?phone=%%CallerNumber%%` and use the drop down box beneath Caller number format to `[National digits only] 3334445555`
**NOTE** It can be frustrating if you have it set to always pop, so the best way to to ensure your 8x8 Work app is set to `Pop-up when incoming call is answered` however you also have to make sure that the 8x8 Work application is set to utilize deskphone (unless you answer from the computer and do not use the desk phone)

## Author

Made with ❤️ by Steven Olsen

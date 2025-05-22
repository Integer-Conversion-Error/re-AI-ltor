import requests
import json
from cookie_retriever import get_realtor_cookie # Assuming cookie_retriever.py is in the same directory or accessible via PYTHONPATH

CONFIG_FILE_PATH = 'config.json'
API_DEFAULTS = {}

def load_config():
    global API_DEFAULTS
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_data = json.load(f)
            API_DEFAULTS = config_data.get('realtor_api_defaults', {})
        print("Configuration loaded successfully.")
    except FileNotFoundError:
        print(f"Warning: Configuration file '{CONFIG_FILE_PATH}' not found. Using hardcoded defaults.")
        # Define fallback defaults if config is missing, though ideally it should exist
        API_DEFAULTS = {
            "Sort": "6-D", "PropertyTypeGroupID": "1", "TransactionTypeId": "2",
            "PropertySearchTypeId": "0", "Currency": "CAD", "IncludeHiddenListings": False,
            "ApplicationId": "1", "CultureId": "1", "Version": "7.0",
            "DefaultRecordsPerPage": 12, "DefaultZoomLevel": 15
        }
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from '{CONFIG_FILE_PATH}'. Using hardcoded defaults.")
        API_DEFAULTS = {
            "Sort": "6-D", "PropertyTypeGroupID": "1", "TransactionTypeId": "2",
            "PropertySearchTypeId": "0", "Currency": "CAD", "IncludeHiddenListings": False,
            "ApplicationId": "1", "CultureId": "1", "Version": "7.0",
            "DefaultRecordsPerPage": 12, "DefaultZoomLevel": 15
        }

load_config() # Load config when module is imported

FALLBACK_COOKIE_FILE_PATH = 'MapSearchAPI_Header.json'

def load_fallback_cookie():
    """Loads the fallback cookie from MapSearchAPI_Header.json."""
    try:
        with open(FALLBACK_COOKIE_FILE_PATH, 'r') as f:
            data = json.load(f)
            # Assuming the cookie is under "Request Headers" -> "cookie"
            cookie_value = data.get("Request Headers", {}).get("cookie")
            if cookie_value:
                print("Successfully loaded fallback cookie.")
                return cookie_value
            else:
                print("Warning: 'cookie' field not found or empty in fallback cookie file under 'Request Headers'.")
                return None
    except FileNotFoundError:
        print(f"Warning: Fallback cookie file '{FALLBACK_COOKIE_FILE_PATH}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from fallback cookie file '{FALLBACK_COOKIE_FILE_PATH}'.")
        return None
    except Exception as e:
        print(f"Warning: An unexpected error occurred while loading fallback cookie: {e}")
        return None

# It's better to define the base headers and payload structure directly in the code
# or load them from a configuration if they are complex and subject to change.
# For simplicity here, we'll define the necessary parts.

DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.realtor.ca",
    "Referer": "https://www.realtor.ca/",
    "Sec-Ch-Ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"", # Example, might need updates
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"", # Example
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36" # Example
}

REALTOR_API_URL = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"

def fetch_property_listings(
    latitude_max, longitude_max, latitude_min, longitude_min,
    page_number=1,
    zoom_level=None, records_per_page=None,
    sort_order=None, property_type_group_id=None, transaction_type_id=None,
    property_search_type_id=None, currency=None, include_hidden_listings=None,
    application_id=None, culture_id=None, version=None
):
    """
    Fetches property listings from Realtor.ca API.

    Args:
        latitude_max (float): Maximum latitude for the search bounding box.
        longitude_max (float): Maximum longitude for the search bounding box.
        latitude_min (float): Minimum latitude for the search bounding box.
        longitude_min (float): Minimum longitude for the search bounding box.
        zoom_level (int): Zoom level for the map.
        page_number (int): The current page number for pagination.
        records_per_page (int): Number of listings to return per page.
        sort_order (str): Sort order for the listings.
        property_type_group_id (str): Property type group ID.
        transaction_type_id (str): Transaction type ID (e.g., 2 for Resale).
        property_search_type_id (str): Property search type ID.
        currency (str): Currency code.
        include_hidden_listings (bool): Whether to include hidden listings.
        application_id (str): Application ID.
        culture_id (str): Culture ID.
        version (str): API version.

    Returns:
        dict: The JSON response from the API, or None if an error occurs.
    """
    # Use provided values or fall back to config defaults
    current_zoom_level = zoom_level if zoom_level is not None else API_DEFAULTS.get("DefaultZoomLevel", 15)
    current_records_per_page = records_per_page if records_per_page is not None else API_DEFAULTS.get("DefaultRecordsPerPage", 12)
    current_sort_order = sort_order if sort_order is not None else API_DEFAULTS.get("Sort", "6-D")
    current_property_type_group_id = property_type_group_id if property_type_group_id is not None else API_DEFAULTS.get("PropertyTypeGroupID", "1")
    current_transaction_type_id = transaction_type_id if transaction_type_id is not None else API_DEFAULTS.get("TransactionTypeId", "2")
    current_property_search_type_id = property_search_type_id if property_search_type_id is not None else API_DEFAULTS.get("PropertySearchTypeId", "0")
    current_currency = currency if currency is not None else API_DEFAULTS.get("Currency", "CAD")
    current_include_hidden_listings = include_hidden_listings if include_hidden_listings is not None else API_DEFAULTS.get("IncludeHiddenListings", False)
    current_application_id = application_id if application_id is not None else API_DEFAULTS.get("ApplicationId", "1")
    current_culture_id = culture_id if culture_id is not None else API_DEFAULTS.get("CultureId", "1")
    current_version = version if version is not None else API_DEFAULTS.get("Version", "7.0")

    # Define payload first (moved up, original cookie logic removed)
    payload_params = {
        "ZoomLevel": current_zoom_level,
        "LatitudeMax": latitude_max,
        "LongitudeMax": longitude_max,
        "LatitudeMin": latitude_min,
        "LongitudeMin": longitude_min,
        "Sort": current_sort_order,
        "PropertyTypeGroupID": current_property_type_group_id,
        "TransactionTypeId": current_transaction_type_id,
        "PropertySearchTypeId": current_property_search_type_id,
        "Currency": current_currency,
        "IncludeHiddenListings": str(current_include_hidden_listings).lower(),
        "RecordsPerPage": current_records_per_page,
        "ApplicationId": current_application_id,
        "CultureId": current_culture_id,
        "Version": current_version,
        "CurrentPage": page_number
    }
    payload_str = "&".join([f"{key}={value}" for key, value in payload_params.items()])

    # Define initial headers (without cookie)
    initial_headers = DEFAULT_HEADERS.copy()

    # --- Capture initial request details (before cookie attempt) ---
    request_details_to_save = {
        "url": REALTOR_API_URL,
        "headers_before_cookie": initial_headers, # Headers without cookie
        "payload_params": payload_params,
        "payload_str": payload_str
    }
    try:
        with open('intercepted_request.json', 'w') as f_json:
            json.dump(request_details_to_save, f_json, indent=4)
        print("Successfully saved initial intercepted request details to intercepted_request.json")
    except IOError as e:
        print(f"Error saving initial intercepted request details: {e}")
    # --- End capture initial request details ---

    print("Attempting to fetch property listings...") # Moved this print down

    # Now, attempt to get the cookie
    dynamic_cookie = None
    try:
        print("Retrieving cookie dynamically...")
        dynamic_cookie = get_realtor_cookie()
        if dynamic_cookie:
            print(f"Dynamic cookie retrieved: {dynamic_cookie[:50]}...")
        else:
            print("Failed to retrieve dynamic cookie.")
    except Exception as e:
        print(f"Error during dynamic cookie retrieval: {e}")

    # Determine which cookie to use
    final_cookie_to_use = dynamic_cookie
    if not final_cookie_to_use:
        print("Attempting to load fallback cookie...")
        fallback_cookie = load_fallback_cookie()
        if fallback_cookie:
            final_cookie_to_use = fallback_cookie
            print(f"Using fallback cookie: {fallback_cookie[:50]}...")
        else:
            print("No dynamic or fallback cookie available. Proceeding without cookie (API call may fail).")

    # Prepare final headers for the actual request
    final_headers = initial_headers.copy() # Start with headers that were saved
    if final_cookie_to_use:
        final_headers["Cookie"] = final_cookie_to_use
    # The content-length will be set automatically by requests library for POST data

    print(f"Making POST request to {REALTOR_API_URL}")
    print(f"Payload: {payload_str}")
    # print(f"Final Headers: {final_headers}") # Be cautious printing headers with cookies

    try:
        response = requests.post(REALTOR_API_URL, headers=final_headers, data=payload_str, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        print(f"API request successful. Status: {response.status_code}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred during the request: {req_err}")
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        print(f"Response content: {response.text}")
    return None

if __name__ == '__main__':
    print("Running realtor_client.py directly for testing...")

    # Example coordinates (Ottawa area, similar to payload example)
    lat_max_example = 45.43411
    lon_max_example = -75.68209
    lat_min_example = 45.41715
    lon_min_example = -75.72110

    print(f"Fetching listings for area: Lat({lat_min_example} to {lat_max_example}), Lon({lon_min_example} to {lon_max_example})")
    
    listings_data = fetch_property_listings(
        latitude_max=lat_max_example,
        longitude_max=lon_max_example,
        latitude_min=lat_min_example,
        longitude_min=lon_min_example,
        page_number=1,
        records_per_page=5 # Request fewer records for a quick test
    )

    if listings_data:
        print("\nSuccessfully fetched listings data!")
        # print(json.dumps(listings_data, indent=2)) # Pretty print the JSON
        print(f"Found {listings_data.get('Paging', {}).get('TotalRecords', 0)} total records.")
        results = listings_data.get('Results', [])
        print(f"Displaying first {len(results)} results:")
        for i, listing in enumerate(results):
            listing_id = listing.get('Id', 'N/A')
            address = listing.get('Property', {}).get('Address', {}).get('AddressText', 'N/A')
            price = listing.get('Property', {}).get('Price', 'N/A')
            print(f"  {i+1}. ID: {listing_id}, Address: {address}, Price: {price}")
    else:
        print("\nFailed to fetch listings data.")

    print("\nRealtor client test finished.")

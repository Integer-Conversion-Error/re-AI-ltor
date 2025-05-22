import requests
import json
from playwright.sync_api import sync_playwright

def get_realtor_cookie():
    realtor_api_url = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"
    realtor_payload_for_fetch = "ZoomLevel=15&LatitudeMax=45.43411&LongitudeMax=-75.68209&LatitudeMin=45.41715&LongitudeMin=-75.72110&Sort=6-D&PropertyTypeGroupID=1&TransactionTypeId=2&PropertySearchTypeId=0&Currency=CAD&IncludeHiddenListings=false&RecordsPerPage=12&ApplicationId=1&CultureId=1&Version=7.0&CurrentPage=1"
    initial_realtor_page_url = "https://www.realtor.ca/map#ZoomLevel=15&Center=45.425629%2C-75.701596&LatitudeMax=45.43411&LongitudeMax=-75.68209&LatitudeMin=45.41715&LongitudeMin=-75.72110&Sort=6-D&PropertyTypeGroupID=1&TransactionTypeId=2&PropertySearchTypeId=0&Currency=CAD"

    js_script_to_trigger_fetch = f"""
    fetch('{realtor_api_url}', {{
        method: 'POST',
        headers: {{
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }},
        body: '{realtor_payload_for_fetch}'
    }})
    .then(response => response.json())
    .then(data => console.log('Fetch_Response_Data:', JSON.stringify(data)))
    .catch(error => console.error('Realtor.ca fetch error:', error));
    """

    with sync_playwright() as p:
        browser = None
        try:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            def handle_request(request):
                if "PropertySearch_Post" in request.url:
                    print(f"Intercepted PropertySearch_Post request to: {request.url}")
                    # Save request headers
                    with open("property_search_request_headers.json", "w") as f:
                        json.dump(request.headers, f, indent=4)
                    print("Saved request headers to property_search_request_headers.json")
                    # Save request body (since it's a POST with a known payload)
                    with open("property_search_request_body.txt", "w") as f:
                        f.write(request.post_data)
                    print("Saved request body to property_search_request_body.txt")

            page.on("request", handle_request)

            print(f"Navigating to initial page: {initial_realtor_page_url}")
            page.goto(initial_realtor_page_url, wait_until="networkidle", timeout=30000)
            print("Initial navigation complete.")

            print("Making PropertySearch_Post request directly...")
            # Make the POST request directly using page.request
            response = page.request.post(
                realtor_api_url,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                },
                data=realtor_payload_for_fetch
            )
            print("PropertySearch_Post request initiated.")

            # Process the response directly
            if response.ok:
                print(f"PropertySearch_Post response received with status: {response.status}")
                # Save response headers
                with open("property_search_response_headers.json", "w") as f:
                    json.dump(response.headers, f, indent=4)
                print("Saved response headers to property_search_response_headers.json")
                # Save response body
                try:
                    response_body = response.json()
                    with open("property_search_response_body.json", "w") as f:
                        json.dump(response_body, f, indent=4)
                    print("Saved response body to property_search_response_body.json")
                except Exception as e:
                    print(f"Could not parse response body as JSON: {e}")
                    with open("property_search_response_body.txt", "w") as f:
                        f.write(response.text())
                    print("Saved response body as text to property_search_response_body.txt")
            else:
                print(f"PropertySearch_Post request failed with status: {response.status}")
                print(f"Response text: {response.text()}")

            # Retrieve all cookies from the browser context after the request
            all_cookies = page.context.cookies()
            captured_cookie = None
            for cookie in all_cookies:
                # Prioritize cookies that seem relevant for session/tracking
                if "realtor.ca" in cookie['domain']:
                    if "visid_incap" in cookie['name'] or "nlbi_" in cookie['name'] or "incap_ses" in cookie['name']:
                        captured_cookie = f"{cookie['name']}={cookie['value']}"
                        break
            
            # If no specific security cookie is found, try to get a general session cookie
            if not captured_cookie:
                for cookie in all_cookies:
                    if "realtor.ca" in cookie['domain'] and "ASP.NET_SessionId" in cookie['name']:
                        captured_cookie = f"{cookie['name']}={cookie['value']}"
                        break
                    elif "realtor.ca" in cookie['domain'] and "realtor.ca_session" in cookie['name']:
                        captured_cookie = f"{cookie['name']}={cookie['value']}"
                        break

            if captured_cookie:
                print(f"Successfully captured cookie: {captured_cookie}")
                with open("realtor_cookie.txt", "w") as f:
                    f.write(captured_cookie)
                print("Saved captured cookie to realtor_cookie.txt")
                return captured_cookie
            else:
                print("Failed to capture a relevant cookie for Realtor.ca.")
                raise Exception("Failed to capture a relevant cookie.")

        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        finally:
            if browser:
                print("Closing browser...")
                browser.close()
                print("Browser closed.")

if __name__ == '__main__':
    print("Attempting to retrieve Realtor.ca cookie...")
    cookie = get_realtor_cookie()

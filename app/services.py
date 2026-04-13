import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException

def fetch_api_data(url: str, params: dict = None, headers: dict = None):
    """
    Calls a third-party API and processes the JSON response with error handling.
    """
    try:
        # Setting a timeout is best practice to prevent the process from hanging
        response = requests.get(url, params=params, headers=headers, timeout=10)

        # Raises an HTTPError if the response status code is 4XX or 5XX
        response.raise_for_status()

        # Process and return the JSON data
        return response.json()

    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except Timeout as timeout_err:
        print(f"The request timed out: {timeout_err}")
    except RequestException as req_err:
        print(f"An unexpected error occurred: {req_err}")
    except ValueError:
        print("Response content is not valid JSON")
    
    return None

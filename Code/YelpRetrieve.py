
import requests
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode
import csv
import Dependencies

# OAuth credential placeholders that must be filled in by users.
# You can find them on
# https://www.yelp.com/developers/v3/manage_app




# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'


# Defaults
DEFAULT_TERM = 'restaurants'
DEFAULT_LOCATION = 'Columbus'
SEARCH_LIMIT = 50
OFFSET = 0



#output array
gathered_data = []


def obtain_bearer_token(host, path):
    """Given a bearer token, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        str: OAuth bearer token, obtained using client_id and client_secret.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    assert Dependencies.CLIENT_ID, "Please supply your client_id."
    assert  Dependencies.CLIENT_SECRET, "Please supply your client_secret."
    data = urlencode({
        'client_id':  Dependencies.CLIENT_ID,
        'client_secret':  Dependencies.CLIENT_SECRET,
        'grant_type': GRANT_TYPE,
    })
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }
    response = requests.request('POST', url, data=data, headers=headers)
    bearer_token = response.json()['access_token']
    return bearer_token


def request(host, path, bearer_token, url_params):
    """Given a bearer token, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        bearer_token (str): OAuth bearer token, obtained using client_id and client_secret.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % bearer_token,
    }
    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


def search(bearer_token, term, location, offset,category):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT,
        'offset': offset,
        'categories': category
    }
    return request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)

def query_api(term, location, offset,category_filter):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
        category_filter (str) : The category of business to query
    """
    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)

    response = search(bearer_token, term, location, offset,category_filter)

    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(category_filter, location))
        return True

    for business in businesses:
        if 'price' in business.keys():
            gathered_data.append([business['id'],business['rating'],business['review_count'],business['categories'],
                                  business['location'],business['coordinates'],business['price']])
        else:
            gathered_data.append([business['id'], business['rating'], business['review_count'], business['categories'],
                                  business['location'], business['coordinates'], 'No recorded price'])
    return len(businesses) != 50;


def main():

    for category in Dependencies.alias_list:
        print("Category Querying: ",category)
        end_reached = False;
        offset = 1;
        while not end_reached:
            try:
                end_reached = query_api(DEFAULT_TERM, DEFAULT_LOCATION, offset,category)
                offset += 50
            except HTTPError as error:
                sys.exit(
                    'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                        error.code,
                        error.url,
                        error.read(),
                    )
                )

    nodup_data = []
    for row in gathered_data:
        if row not in nodup_data:
            nodup_data.append(row)

    with open(Dependencies.outfile_path,'w',newline='') as f:
        out_writer = csv.writer(f)
        out_writer.writerow(["Name","Rating","Number of Reviews","Category","Address","Lat/Long","Price"])
        for row in nodup_data:
                out_writer.writerow(row)
    f.close()

main()

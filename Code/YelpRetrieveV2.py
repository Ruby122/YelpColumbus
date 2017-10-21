import requests
from urllib.parse import quote
from urllib.parse import urlencode
import csv
import Scripts.Dependencies as Dependencies

# OAuth credential placeholders that must be filled in by users.
# You can find them ons
# https://www.yelp.com/developers/v3/manage_app




# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'


# Defaults
DEFAULT_TERM = 'food'
DEFAULT_LOCATION = 'Columbus'
SEARCH_LIMIT = 50
OFFSET = 0


#output array for general data
gathered_data = []

#output array for review data
review_data = []


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
    while response.status_code == 504:
        response = requests.request('GET', url, headers=headers, params=url_params)
        print(response, "Retrying Request")
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
    while response.status_code == 504:
        response = requests.request('GET', url, headers=headers, params=url_params)
        print(response)
    return response.json()


def search_reviews(bearer_token,business):
        review_path = BUSINESS_PATH + business + "/reviews"
        print(review_path)
        return request(API_HOST,review_path,bearer_token,{})

def search(bearer_token, term, location, offset,category):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT,
        'offset': offset,
        'categories': category
    }
    return request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)

def query_reviews(restaurant_id):
    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)
    response = search_reviews(bearer_token,restaurant_id)
    #print(response)
    reviews = response.get('reviews')
    #print(reviews)
    if not response:
        print('No reviews found for ',restaurant_id)
    else:
        lenth = 0
        if response['total'] > 2:
            length = 3
        else:
            length = response['total']
        data_row = [restaurant_id,response['total']]
        for review in range(0,length):
            data_row.append(reviews[review]['user'])
            data_row.append(reviews[review]['time_created'])
            data_row.append(reviews[review]['rating'])
            data_row.append(reviews[review]['text'])
            #print(data_row)
        review_data.append(data_row)


def query_businesses(term, location, offset,category_filter):
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
            end_reached = query_businesses(DEFAULT_TERM, DEFAULT_LOCATION, offset,category)
            offset += 50

    nodup_data = []
    for row in gathered_data:
        if row not in nodup_data:
            nodup_data.append(row)


    for row in nodup_data:
        query_reviews(row[0])

    with open(Dependencies.yelp_general_outfile_path, 'w', newline='') as f:
        out_writer = csv.writer(f)
        out_writer.writerow(["Name","Rating","Number of Reviews","Category","Address","Lat/Long","Price"])
        for row in nodup_data:
            out_writer.writerow(row)
    f.close()

    with open(Dependencies.reviews_outfile_path,'w', newline='') as g:
        reviews_writer = csv.writer(g)
        print(len(review_data))
        #print(review_data)
        reviews_writer.writerow(["ID","Total Number of Reviews","Review 1 URL/Name", "DateTime 1","Score 1","Review Segment 1","Review 2 URL/Name", "DateTime 2","Score 2","Review Segment 2","Review 3 URL/Name", "DateTime 3","Score 3","Review Segment 3"])
        for element in review_data:
                reviews_writer.writerow(element)
    g.close()


main()

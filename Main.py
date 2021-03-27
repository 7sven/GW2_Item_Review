import urllib.request, json

url_item_ids = 'https://api.guildwars2.com//v2/commerce/prices'

"""
function to get all the item ids from the items available on the trading post
using urllib to request the content of the web api and the using json to interpret the data
"""


def get_all_ids():
    response_item_ids = urllib.request.urlopen(url_item_ids)

    data_item_ids = json.loads(response_item_ids.read())

    return data_item_ids


"""
function to get the information of each of the items in the trading post
this includes the buy and sell quantity and unit_prices
"""


def get_prices(ids_to_check):
    items_with_prices = []
    i = 0
    while i < len(ids_to_check):
        id = ",".join([str(elem) for elem in ids_to_check[i:i+200]])
        response_prices = urllib.request.urlopen(url_item_ids + "?ids=" + id)
        item = json.loads(response_prices.read())
        items_with_prices += item
        i += 200
        print(i)

    """
    for id in ids_to_check:
        response_prices = urllib.request.urlopen(url_item_ids + "/" + str(id))
        item = json.loads(response_prices.read())
        print(item)
        items_with_prices.append(item)
    return items_with_prices
    """

test = get_all_ids()
get_prices(test)

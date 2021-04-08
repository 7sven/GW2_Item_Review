import urllib.request, json, sqlite3

url_item_ids = 'https://api.guildwars2.com//v2/commerce/prices'
url_item_name = 'https://api.guildwars2.com/v2/items?ids='

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
using 200 steps since the api can't handle more than 200 id calls at once.
this results in a reduction of several thousands website calls. Before I called it each on it own which resulted in 
around 30.000 calls. This was reduced to around 150 calls.
"""


def get_prices(ids_to_check):
    items_with_prices = []
    iterator_all_ids = 0
    while iterator_all_ids < len(ids_to_check):
        id = ",".join([str(elem) for elem in ids_to_check[iterator_all_ids:iterator_all_ids + 200]])
        response_prices = urllib.request.urlopen(url_item_ids + "?ids=" + id)
        response_item_info = urllib.request.urlopen(url_item_name + id)
        all_200_items = json.loads(response_prices.read())
        all_200_names = json.loads(response_item_info.read())
        item_reduced = []
        for i in range(len(all_200_names)):
            if (all_200_names[i]['id'] == all_200_items[i]['id']):
                profit = int(
                    (all_200_items[i]['sells']['unit_price'] - (all_200_items[i]['sells']['unit_price'] * 0.15)) -
                    all_200_items[i]['buys']['unit_price'])
                if all_200_items[i]['buys']['unit_price'] != 0:
                    roi = int(((profit / all_200_items[i]['buys']['unit_price']) * 10000) // 100)
                else:
                    roi = int(0)
                item_reduced.append(
                    [all_200_items[i]['id'], all_200_names[i]['name'], all_200_items[i]['buys']['unit_price'],
                     all_200_items[i]['sells']['unit_price'], profit, roi])
        items_with_prices += item_reduced
        iterator_all_ids += 200
    return items_with_prices


if __name__ == '__main__':
    connect = sqlite3.connect('profit_table.db')
    cursor = connect.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY,
        name TEXT,
        buy INTEGER,
        sell INTEGER,
        profit INTEGER,
        roi INTEGER)''')

    get_id = get_all_ids()
    items = get_prices(get_id)

    #cursor.executemany('INSERT INTO items VALUES (?,?,?,?,?)*, items') need to look into how to do this

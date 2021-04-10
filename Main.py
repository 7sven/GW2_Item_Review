import urllib.request, json, sqlite3, tkinter as tk
from tkinter import ttk

url_item_ids = 'https://api.guildwars2.com//v2/commerce/prices'
url_item_name = 'https://api.guildwars2.com/v2/items?ids='

"""
function to get all the item ids from the items available on the trading post
using urllib to request the content of the web api and the using json to interpret the data
return: all ids from items that are available on the trading post
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

get: all ids that needs to be reviewd
return: list of lists in which each list contains id, name, sell and buy price, profit from flipping and the roi
"""


def get_prices(ids_to_check):
    popup = tk.Toplevel()
    tk.Label(popup, text="Updating data base").grid(row=0, column=0, padx='5', pady='5')
    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(popup, orient='horizontal', mode="determinate", maximum=30000, variable=progress_var)
    progress.grid(row=1, column=0, pady='5', padx='5')
    popup.group(window)
    popup.pack_slaves()
    items_with_prices = []
    iterator_all_ids = 0
    progress.start()
    while iterator_all_ids < len(ids_to_check):
        popup.update()
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
                    (all_200_items[i]['id'], all_200_names[i]['name'], all_200_items[i]['buys']['unit_price'],
                     all_200_items[i]['sells']['unit_price'], profit, roi))
        items_with_prices += item_reduced
        iterator_all_ids += 200
        progress_var.set(iterator_all_ids)
    progress.stop()
    return items_with_prices


"""
function which gets all possible ids, then get their information and updates the db
"""


def update_db():
    get_id = get_all_ids()
    items = get_prices(get_id)
    cursor.executemany('INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?)', items)
    connect.commit()


def get_search():
    pass


"""
main function which enables a connection to the db and currently prints out all items in the dbS
"""
if __name__ == '__main__':
    connect = sqlite3.connect('profit_table.db')
    cursor = connect.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        buy INTEGER,
        sell INTEGER,
        profit INTEGER,
        roi INTEGER)''')

    window = tk.Tk()
    window.title("Guild Wars 2 Item Profit Review")
    window.geometry("700x700")

    min_label = tk.Label(text="minimum buying price")
    max_label = tk.Label(text="maximum buying price")
    minimum_gold_price = ttk.Entry(width=5)
    minimum_silver_price = ttk.Entry(width=5)
    minimum_copper_price = ttk.Entry(width=5)
    maximum_gold_price = ttk.Entry(width=5)
    maximum_silver_price = ttk.Entry(width=5)
    maximum_copper_price = ttk.Entry(width=5)
    update_button = tk.Button(text="update data base", width=20, command=update_db)
    get_results = tk.Button(text='search', width=5, command=get_search)
    sort_after = ttk.Combobox(window, width=50, values=[
        "sort after highest return of investment",
        "sort cheapest to most expensive",
        "sort most expansive to cheapest",
        "sort after highest profit"
    ])
    results = ttk.Treeview()

    min_label.grid(column=0, row=2, padx='5', pady='5', sticky='w')
    minimum_gold_price.grid(column=1, row=2, padx='5', pady='5', sticky='w')
    minimum_silver_price.grid(column=2, row=2, padx='5', pady='5', sticky='w')
    minimum_copper_price.grid(column=3, row=2, padx='5', pady='5', sticky='w')
    max_label.grid(column=4, row=2, padx='5', pady='5', sticky='w')
    maximum_gold_price.grid(column=5, row=2, padx='5', pady='5', sticky='w')
    maximum_silver_price.grid(column=6, row=2, padx='5', pady='5', sticky='w')
    maximum_copper_price.grid(column=7, row=2, padx='5', pady='5', sticky='w')
    get_results.grid(column=7, row=3)
    sort_after.grid(column=0, columnspan=8, row=3)
    update_button.grid(column=0, row=1, padx='5', pady='5', sticky='w')
    results.grid(column=0, row=4, columnspan=9, padx='5', pady='5', sticky='NESW')

    window.mainloop()

    connect.close()

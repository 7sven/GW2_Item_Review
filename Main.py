import urllib.request, json, sqlite3, tkinter as tk
from tkinter import ttk

url_item_ids = 'https://api.guildwars2.com//v2/commerce/prices'
url_item_name = 'https://api.guildwars2.com/v2/items?ids='
interrupt = False

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


def get_prices(ids_to_check, popup, progress_var):
    global interrupt
    items_with_prices = []
    iterator_all_ids = 0
    while iterator_all_ids < len(ids_to_check) and not interrupt:
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
    return items_with_prices


"""
helper function, so that i can cancel the data base update
"""


def interrupt_update():
    global interrupt
    interrupt = True


"""
function which gets all possible ids, then get their information and updates the db, also shows the progress on a 
popup window
"""


def update_db():
    global interrupt
    popup = tk.Toplevel(takefocus=True)
    popup.geometry("100x100+%d+%d" % (window.winfo_x() + 100, window.winfo_y() + 100))
    tk.Label(popup, text="Updating data base").grid(row=0, column=0, padx='5', pady='5')
    tk.Button(popup, text="cancle", command=interrupt_update).grid(row=3, column=0)
    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(popup, orient='horizontal', mode="determinate", maximum=30000, variable=progress_var)
    progress.grid(row=1, column=0, pady='5', padx='5')
    popup.group(window)
    popup.pack_slaves()
    progress.start()

    popup.protocol("WM_DELETE_WINDOW", interrupt_update)
    interrupt = False

    get_id = get_all_ids()
    items = get_prices(get_id, popup, progress_var)
    progress.stop()
    popup.destroy()
    cursor.executemany('INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?)', items)
    connect.commit()


"""
helper function which combines the strings to make them search able in the database
"""


def combine_number(gold, silver, copper):
    if not gold:
        gold = "0"
    if not silver:
        silver = "00"
    if not copper:
        copper = "00"
    if len(silver) == 1:
        silver = "0" + silver
    if len(copper) == 1:
        copper = "0" + copper
    return gold + silver + copper
    pass


"""
helper function to make the db query and make the result into a text 
return: text of 20 items corresponding to the query
"""


def query(sorting: str, comb_min: int, comb_max: int) -> str:
    sort = {"sort by return of investment": "roi DESC", "sort cheapest to most expensive": "buy",
            "sort most expansive to cheapest": "buy DESC", "sort by highest profit": "profit DESC"}

    res = cursor.execute(
        """SELECT * FROM items WHERE buy >= {} AND buy <= {} AND profit > 0 ORDER BY {}""".format(comb_min,
                                                                                                             comb_max,
                                                                                                             sort[
                                                                                                                 sorting]))
    text = ""
    for i in res:
        buy = "{}g {}s {}s".format(i[2]//10000,(i[2]%10000)//100,(i[2]%1000)%100)
        sell = "{}g {}s {}s".format(i[3]//10000,(i[3]%10000)//100,(i[3]%1000)%100)
        profit = "{}g {}s {}s".format(i[4]//10000,(i[4]%10000)//100,(i[4]%1000)%100)

        text += "{} | buy price = {} | sell price = {} | profit = {} | roi = {}%\n\n".format(i[1], buy, sell, profit, i[5])
    return text


"""
function which gets all the values from the gui and in the end stows a result into the text field
"""


def get_search():
    sorting = sort_by.get()
    results.configure(state='normal')
    results.delete('1.0', 'end')
    results.configure(state='disabled')
    min_gold = minimum_gold_price.get()
    min_silver = minimum_silver_price.get()
    min_copper = minimum_copper_price.get()
    max_gold = maximum_gold_price.get()
    max_silver = maximum_silver_price.get()
    max_copper = maximum_copper_price.get()
    if len(min_copper) > 2 or len(min_silver) > 2 or len(max_silver) > 2 or len(max_copper) > 2 or not sorting:
        results.configure(state='normal')
        results.insert('end', "A given value is to long or you didn't chose the sorting method")
        results.configure(state='disabled')
        return
    comb_min = combine_number(min_gold, min_silver, min_copper)
    comb_max = combine_number(max_gold, max_silver, max_copper)
    try:
        comb_min = int(comb_min)
        comb_max = int(comb_max)
    except TypeError:
        results.configure(state='normal')
        results.insert('end', "A given value is not a number")
        results.configure(state='disabled')
        return
    text_to_print = query(sorting, comb_min, comb_max)
    results.configure(state='normal')
    results.insert('end', text_to_print)
    results.configure(state='disabled')


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
    gold1 = tk.Label(text="gold")
    gold2 = tk.Label(text="gold")
    silver1 = tk.Label(text="silver")
    silver2 = tk.Label(text="silver")
    copper1 = tk.Label(text="copper")
    copper2 = tk.Label(text="copper")
    minimum_gold_price = ttk.Entry(width=5)
    minimum_silver_price = ttk.Entry(width=5)
    minimum_copper_price = ttk.Entry(width=5)
    maximum_gold_price = ttk.Entry(width=5)
    maximum_silver_price = ttk.Entry(width=5)
    maximum_copper_price = ttk.Entry(width=5)
    update_button = tk.Button(text="update data base", width=20, command=update_db)
    get_results = tk.Button(text='search', width=5, command=get_search)
    sort_by = ttk.Combobox(window, width=50, values=[
        "sort by return of investment",
        "sort cheapest to most expensive",
        "sort most expansive to cheapest",
        "sort by highest profit"
    ])
    results = tk.Text(state='disabled', font=("Arial", 8))
    scroll = ttk.Scrollbar(command=results.yview)
    results.configure(state='normal')
    results['yscrollcommand']= scroll.set

    min_label.grid(column=0, row=2, padx='5', pady='5', sticky='w')
    minimum_gold_price.grid(column=1, row=2, padx='5', pady='5', sticky='w')
    minimum_silver_price.grid(column=2, row=2, padx='5', pady='5', sticky='w')
    minimum_copper_price.grid(column=3, row=2, padx='5', pady='5', sticky='w')
    gold1.grid(column=1, row=1, padx='5', pady='5', sticky='w')
    silver1.grid(column=2, row=1, padx='5', pady='5', sticky='w')
    copper1.grid(column=3, row=1, padx='5', pady='5', sticky='w')
    max_label.grid(column=4, row=2, padx='5', pady='5', sticky='w')
    maximum_gold_price.grid(column=5, row=2, padx='5', pady='5', sticky='w')
    maximum_silver_price.grid(column=6, row=2, padx='5', pady='5', sticky='w')
    maximum_copper_price.grid(column=7, row=2, padx='5', pady='5', sticky='w')
    gold2.grid(column=5, row=1, padx='5', pady='5', sticky='w')
    silver2.grid(column=6, row=1, padx='5', pady='5', sticky='w')
    copper2.grid(column=7, row=1, padx='5', pady='5', sticky='w')
    get_results.grid(column=7, row=3)
    sort_by.grid(column=0, columnspan=8, row=3)
    update_button.grid(column=0, row=1, padx='5', pady='5', sticky='w')
    results.grid(column=0, row=4, columnspan=300, padx='5', pady='5', sticky='NESW')
    scroll.grid(column=9,row=4, rowspan=3, padx='5', pady='5', sticky='nsew')
    window.grid_columnconfigure(0,weight=1)
    window.mainloop()

    connect.close()

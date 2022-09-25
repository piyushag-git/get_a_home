import pytest
import requests
import random
from datetime import date, timedelta
from unittest.mock import Mock
from requests.models import Response
from string import ascii_lowercase, digits

from app import format_prices_by_year, format_all_prices, get_postcodes, attach_long_lat_to_prices

def test_get_postcodes():
    position = {"lat": "50.84120684080165", "long": "-0.13691759734549602" }
    res = requests.get(
        "https://api.postcodes.io/postcodes?lon={}&lat={}&limit=99&radius=200".format(position['long'], position['lat']))
    print(res)
    assert res.status_code == 200

def get_ran_pcs(num):
    chars = ascii_lowercase + digits
    return [''.join(random.choice(chars) for _ in range(7)) for _ in range(num)]

def get_ran_lats(num):
    return [random.uniform(-90,90) for _ in range(num)]

def get_ran_longs(num):
    return [random.uniform(-180,180) for _ in range(num)]

def get_ran_prices(num):
    return [str(random.randint(0,100000)) for _ in range(num)]

def get_ran_dates(num):
    start_date = date(1995, 1, 1)
    end_date = date(2022, 1, 1)
    
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days    

    return [str(start_date + timedelta(days=random.randrange(days_between_dates))) for _ in range(num)]

def get_ran_avg_prices(num):
    return [random.uniform(0,100000) for _ in range(num)]


def dummy_sparql(postcodes, amounts, dates):
    """
    dummy_sparql creates a mock output from get_prices() in app.py to be used as test input
    :param postcodes: list of strings representing postcodes
    :param amounts: list of strings representing sale prices
    :param dates: list of dates in form 'YYYY-__-__'
    :return: dict as in get_prices() in app.py
    """ 

    bindings = []
    for p, a, d in zip(postcodes, amounts, dates):
        bindings.append(
            {
                "postcode" : {
                    "value" : p
                },
                "amount" : {
                    "value" : a
                },
                "date" : {
                    "value" : d
                }        
            }
        )
    return {"results" : {
            "bindings" : bindings
            }
        }


def dummy_postcodes(postcodes, lats, longs):
    """
    dummy_postcodes creates a mock output from get_postcodes() in app.py to be used as test input
    :param postcodes: list of strings representing postcodes
    :param lats: list of floats representing latitudes
    :param longs: list of floats representing longitudes
    :return: dict as in get_postcodes() in app.py
    """ 

    dummy = Mock(spec=Response)
    dummy.status_code = 200

    values = []
    pc_list = []
    for p, lat, long in zip(postcodes, lats, longs):
        pc_list.append(p)
        values.append({"postcode" : p, "latitude": lat, "longitude": long })

    dummy.json.return_value = {"result" : values}

    return {"list": pc_list, "data": dummy}


def expected_output(postcodes, lats, longs, avg_prices):
    """
    expected_output creates output in same form as format_all_prices() in app.py to be used as expected test output
    :param postcodes: list of strings representing postcodes
    :param lats: list of floats representing latitudes
    :param longs: list of floats representing longitudes
    :param avg_prices: list of floats representing avg prices
    :return: dict as in get_postcodes() in app.py
    """ 

    res = {}

    for pc, lat, long, ap in zip(postcodes, lats, longs, avg_prices):
        res[pc] = { "lat": lat, "long": long, "avg_price": ap}
    
    return res

def expected_output_by_year(postcodes, lats, longs, avg_prices, years, years_per_pc):
    """
    expected_output creates output in same form as format_prices_by_year() in app.py to be used as expected test output
    :param postcodes: list of strings representing postcodes
    :param lats: list of floats representing latitudes
    :param longs: list of floats representing longitudes
    :param avg_prices: list of floats representing avg prices
    :param years: list of strings representing years or dates in form YYYY-__-__
    :param years_per_pc: list of integers representing #years there is data for for each pc
    :return: dict as in get_postcodes() in app.py
    """ 

    res = {}
    idx = 0
    for pc, lat, long, ys in zip(postcodes, lats, longs, years_per_pc):
        res[pc] = { "lat": lat, "long": long, "years": {}}
        ap_list = []
        for ap, y in zip(avg_prices[idx:idx+ys], years[idx:idx+ys]):
            if y[0:4] not in res[pc]['years']:
                res[pc]['years'][y[0:4]] = [ap]
            else:
                res[pc]['years'][y[0:4]].append(ap)
            idx = idx+1
        

    return res


def get_tests_attach_long_lat_to_prices():
    # Partitioning:
    # - input length: 0, 1, >1
    
    random.seed(3)

    tests = []  

    ## Empty input
    data_in = expected_output([], [], [], [])
    postcodes = dummy_postcodes([], [], [])
    data_out = expected_output([], [], [], [])
    tests.append((postcodes['data'].json()['result'], data_in, data_out))
    
    # Input length 1
    input_length = 1
    
    pc_list = get_ran_pcs(input_length)
    lats = get_ran_lats(input_length)
    longs = get_ran_longs(input_length)

    avg_prices = [-1]*input_length # Irrelevant for this test

    data_in = expected_output(pc_list, [0]*input_length, [0]*input_length, avg_prices)
    postcodes = dummy_postcodes(pc_list, lats, longs)
    data_out = expected_output(pc_list, lats, longs, avg_prices)
    
    tests.append((postcodes['data'].json()['result'], data_in, data_out))

    # Input length > 1
    input_length = 100    
    pc_list = get_ran_pcs(input_length)
    lats = get_ran_lats(input_length)
    longs = get_ran_longs(input_length)

    avg_prices = [-1]*input_length # Irrelevant for this test

    data_in = expected_output(pc_list, [0]*input_length, [0]*input_length, avg_prices)
    postcodes = dummy_postcodes(pc_list, lats, longs)
    data_out = expected_output(pc_list, lats, longs, avg_prices)
    
    tests.append((postcodes['data'].json()['result'], data_in, data_out))

    return tests
   
    
@pytest.mark.parametrize("postcodes,data,expected", get_tests_attach_long_lat_to_prices())
def test_attach_long_lat_to_prices(postcodes, data, expected):
    res = attach_long_lat_to_prices(postcodes, data)
    assert res == expected


def get_tests_format_all_prices():
    # Partitioning:
    # - input length: 0, 1, >1
    # - missing price data: y/n
    # - at most one sale per postcode: y/n
    
    random.seed(3)

    tests = []  

    ## Empty input
    price_data = dummy_sparql([], [], [])
    pc_data = dummy_postcodes([], [], [])["data"]
    expected = expected_output([], [], [], [])
    tests.append((pc_data, price_data, expected))

    ## Input length = 1, no missing data, at most one sale per postcode
    input_length = 1
    pc_list = ['BN1 9RU']
    lats = get_ran_lats(input_length)
    longs = get_ran_longs(input_length)
    prices = ['10']
    dates = get_ran_dates(input_length)
    avg_prices = [10]

    price_data = dummy_sparql(pc_list, prices, dates)
    pc_data = dummy_postcodes(pc_list, lats, longs)["data"]
    expected = expected_output(pc_list, lats, longs, avg_prices)
    tests.append((pc_data, price_data, expected))

    ## Input length > 1, missing data, at most one sale per postcode
    input_length = 3
    indeces = [0, 2] # idxs corresponding to postcodes from pc_list where there is a sale
    pc_list = ['BN1 9RU', 'HF4 8FT', 'GGG FFF']
    pc_list_prices = [pc_list[index] for index in indeces]
    lats_in = get_ran_lats(input_length)
    longs_in = get_ran_longs(input_length)
    lats_out = [lats_in[index] for index in indeces]
    longs_out = [longs_in[index] for index in indeces]
    prices = ['10', '5']
    dates = get_ran_dates(input_length)
    avg_prices = [10, 5]

    price_data = dummy_sparql(pc_list_prices, prices, dates)
    pc_data = dummy_postcodes(pc_list, lats_in, longs_in)["data"]
    expected = expected_output(pc_list_prices, lats_out, longs_out, avg_prices)
    tests.append((pc_data, price_data, expected))


    ## input length > 1, no missing data, more than one sale per postcode
    input_length = 3
    data_length = 6 # sparql returns 6 bindings
    indeces = [0, 0, 0, 1, 1, 2] # idxs corresponding to sales in a postcode
    pc_list = ['BN1 9RU', 'HF4 8FT', 'GGG FFF']
    pc_list_prices = [pc_list[index] for index in indeces]
    lats = get_ran_lats(input_length)
    longs = get_ran_longs(input_length)
    
    prices = ['10', '5', '3', '20', '10', '99']
    dates = get_ran_dates(data_length)
    avg_prices = [6, 15, 99]

    price_data = dummy_sparql(pc_list_prices, prices, dates)
    pc_data = dummy_postcodes(pc_list, lats, longs)["data"]
    expected = expected_output(pc_list, lats, longs, avg_prices)
    tests.append((pc_data, price_data, expected))

    return tests

@pytest.mark.parametrize("postcodes,price_data,expected", get_tests_format_all_prices())
def test_format_all_prices(postcodes, price_data, expected):
    res = format_all_prices(postcodes, price_data)
    assert res == expected


def get_tests_format_prices_by_year():
    # Partitioning:
    # - input length: 0, 1, >1
    # - missing price data: y/n
    # - at most one sale per postcode: y/n
    # - at most one sale per year per postcode: y/n

    tests = []

    ## Empty input
    price_data = dummy_sparql([], [], [])
    pc_data = dummy_postcodes([], [], [])["data"]
    expected = expected_output_by_year([], [], [], [], [], [])
    tests.append((pc_data, price_data, expected))

    # input length 1, n, y, y
    input_length = 1
    pc_list = ['BN1 9RU']
    lats = get_ran_lats(input_length)
    longs = get_ran_longs(input_length)
    prices = ['10']
    dates = get_ran_dates(input_length)
    avg_prices = [10]

    price_data = dummy_sparql(pc_list, prices, dates)
    pc_data = dummy_postcodes(pc_list, lats, longs)["data"]
    expected = expected_output_by_year(pc_list, lats, longs, avg_prices, dates, [1])
    tests.append((pc_data, price_data, expected))

    # input length >1 y, y, y
    input_length = 3
    indeces = [0, 2] # idxs corresponding to postcodes from pc_list where there is a sale
    pc_list = ['BN1 9RU', 'HF4 8FT', 'GGG FFF']
    pc_list_prices = [pc_list[index] for index in indeces]
    lats_in = get_ran_lats(input_length)
    longs_in = get_ran_longs(input_length)
    lats_out = [lats_in[index] for index in indeces]
    longs_out = [longs_in[index] for index in indeces]    
    dates = ['2020', '2021']
    years_per_pc = [1, 1]
    prices = ['10', '5']
    avg_prices = [10, 5]

    price_data = dummy_sparql(pc_list_prices, prices, dates)
    pc_data = dummy_postcodes(pc_list, lats_in, longs_in)["data"]
    expected = expected_output_by_year(pc_list_prices, lats_out, longs_out, avg_prices, dates, years_per_pc)
    tests.append((pc_data, price_data, expected))

    # input length >1, n, n, y
    input_length = 3
    data_length = 6 # sparql returns 6 bindings
    indeces = [0, 0, 0, 1, 1, 2] # idxs corresponding to sales in a postcode
    pc_list = ['BN1 9RU', 'HF4 8FT', 'GGG FFF']
    pc_list_prices = [pc_list[index] for index in indeces]
    lats = get_ran_lats(input_length)
    longs = get_ran_longs(input_length)
    dates = get_ran_dates(input_length)
    prices = ['10', '5', '3', '20', '10', '99']
    dates = ['2010', '2011', '2012', '2013', '2014', '2015']
    years_per_pc = [3, 2, 1]
    avg_prices = [10, 5, 3, 20, 10, 99]

    price_data = dummy_sparql(pc_list_prices, prices, dates)
    pc_data = dummy_postcodes(pc_list, lats, longs)["data"]
    expected = expected_output_by_year(pc_list, lats, longs, avg_prices, dates, years_per_pc)
    tests.append((pc_data, price_data, expected))

    # input length >1, n, n, n
    input_length = 3
    data_length = 6 # sparql returns 6 bindings
    indeces = [0, 0, 0, 1, 1, 2] # idxs corresponding to sales in a postcode
    pc_list = ['BN1 9RU', 'HF4 8FT', 'GGG FFF']
    pc_list_prices = [pc_list[index] for index in indeces]
    lats = get_ran_lats(input_length)
    longs = get_ran_longs(input_length)
    dates = get_ran_dates(input_length)
    prices = ['10', '5', '3', '20', '10', '99']
    dates = ['2010', '2010', '2010', '2013', '2014', '2015']
    years_per_pc = [3, 2, 1]
    avg_prices = [10, 5, 3, 20, 10, 99]

    price_data = dummy_sparql(pc_list_prices, prices, dates)
    pc_data = dummy_postcodes(pc_list, lats, longs)["data"]
    expected = expected_output_by_year(pc_list, lats, longs, avg_prices, dates, years_per_pc)
    tests.append((pc_data, price_data, expected))

    return tests

@pytest.mark.parametrize("postcodes,price_data,expected", get_tests_format_prices_by_year())
def test_format_prices_by_year(postcodes, price_data, expected):
    res = format_prices_by_year(postcodes, price_data)
    assert res == expected
import json
import ssl
import urllib.parse
import urllib.request

# noinspection PyUnresolvedReferences
from quantumrandom import *
# noinspection PyProtectedMember
from quantumrandom import DATA_TYPES
# noinspection PyProtectedMember
from quantumrandom import MAX_LEN
# noinspection PyProtectedMember
from quantumrandom import URL

# noinspection PyProtectedMember,PyUnresolvedReferences
ssl._create_default_https_context = ssl._create_unverified_context


def get_json(url):
    return json.loads(urllib.request.urlopen(url).read().decode('ascii'))


def get_data(data_type='uint16', array_length=1, block_size=1):
    """Fetch data from the ANU Quantum Random Numbers JSON API"""
    if data_type not in DATA_TYPES:
        raise Exception("data_type must be one of %s" % DATA_TYPES)
    if array_length > MAX_LEN:
        raise Exception("array_length cannot be larger than %s" % MAX_LEN)
    if block_size > MAX_LEN:
        raise Exception("block_size cannot be larger than %s" % MAX_LEN)
    url = URL + '?' + urllib.parse.urlencode({
        'type': data_type,
        'length': array_length,
        'size': block_size,
    })
    data = get_json(url)
    assert data['success'] is True, data
    assert data['length'] == array_length, data
    return data['data']


# Override the patched functions in the original package
get_json = get_json
get_data = get_data

if __name__ == '__main__':
    print("Testing patch..")
    try:
        print(get_data('hex16', 8, 8))
    except Exception as ex:
        print(f"Caught exception: {ex!r}")
    input("Press ENTER to exit...")

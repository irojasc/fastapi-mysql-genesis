from collections import defaultdict

def get_all_publishers(value):
    index, data = value
    return {
        "index": index,
        "publisher": data[0]
    }

def get_all_pair_company_publishers(data):
    result = defaultdict(list)
    for item in data:
        key = item[1]
        value = item[0]
        result[key].append(value)
    return (dict(result))
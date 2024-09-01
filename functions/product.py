def get_all_publishers(value):
    index, data = value
    return {
        "index": index,
        "publisher": data[0]
    }
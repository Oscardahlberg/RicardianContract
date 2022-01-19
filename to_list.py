
def data_to_list(all_data):
    full_table = []
    for data in all_data:
        table = [data["_id"],
                 data["name"],
                 data["owner"],
                 data["permissions"]["read"],
                 data["permissions"]["modify"],
                 data["permissions"]["delete"]]
        full_table.append(table)
    return full_table

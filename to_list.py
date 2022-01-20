
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


def access_perm_to_list(all_nego, status0, status1):
    full_table = []
    for nego in all_nego:
        if nego["status"] == status0 or nego["status"] == status1:
            table = [nego["_id"],
                     nego["demander"],
                     nego["provider"],
                     nego["creation_date"],
                     nego["offer"],
                     nego["request_details"]["item"],
                     nego["request_details"]["start_date"],
                     nego["request_details"]["end_date"],
                     nego["request_details"]["role"],
                     nego["status"]]
            full_table.append(table)
    return full_table

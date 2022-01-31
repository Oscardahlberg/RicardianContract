
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


def access_perms_to_list(all_nego, status):
    full_table = []
    for nego in all_nego:
        if nego["status"] in status:
            full_table.append(access_perm_to_list(nego))
    return full_table


def access_perm_to_list(nego):
    table = [nego["_id"],                            # 0
             nego["demander"],                       # 1
             nego["provider"],                       # 2
             nego["creation_date"],                  # 3
             nego["offer"],                          # 4
             nego["request_details"]["item"],        # 5
             nego["request_details"]["start_date"],  # 6
             nego["request_details"]["end_date"],    # 7
             nego["request_details"]["role"],        # 8
             nego["status"]]                         # 9
    return table



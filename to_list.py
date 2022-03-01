
def data_to_list(all_data):
    full_table = []
    for data in all_data:
        table = [data["_id"],                       # 0
                 data["name"],                      # 1
                 data["owner"],                     # 2
                 data["permissions"]["read"],       # 3
                 data["permissions"]["modify"],     # 4
                 data["permissions"]["delete"]]     # 5
        full_table.append(table)
    return full_table


def data_dict_to_name_list(all_data):
    full_table = []
    for data in all_data:
        full_table.append(data["name"])
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


def node_list(data_list):

    node_name_list = []
    for node in data_list:
        if node["id"] > 0:
            node_name_list.append(node["name"])

    return node_name_list


def parent_list(data_list):

    links_name_list = []
    for link in data_list:
        if link["parent"]["id"] > 0:
            links_name_list.append(link["parent"]["name"])

    return links_name_list


def child_list(data_list):

    links_name_list = []
    for link in data_list:
        if link["child"]["id"] > 0:
            links_name_list.append(link["child"]["name"])

    return links_name_list




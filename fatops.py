"""
    PyFat file operations here
"""

import sys


def read_cluster(fs, cluster_number):
    return fs.read_cluster_contents(cluster_number)


def write_cluster(fs, cluster_number, data):
    try:
        fs._write_data_to_address(data, fs.get_data_cluster_address(cluster_number))
    except OSError:
        print(f"Failed to write to cluster #{cluster_number}, cluster address {fs.get_data_cluster_address(cluster_number)}")


def device_len(fs):
    last_loc = fs._PyFat__fp.tell()
    rc = fs._PyFat__fp.seek(0, 2)
    fs._PyFat__fp.seek(last_loc)
    return rc


def free_clusters(fs, offset=1):
    min_valid_cluster = fs.FAT_CLUSTER_VALUES[fs.fat_type]['MIN_DATA_CLUSTER']
    max_valid_cluster = fs.FAT_CLUSTER_VALUES[fs.fat_type]['MAX_DATA_CLUSTER']
    free_cluster_value = fs.FAT_CLUSTER_VALUES[fs.fat_type]['FREE_CLUSTER']
    bad_cluster_value = fs.FAT_CLUSTER_VALUES[fs.fat_type]['BAD_CLUSTER']
    device_bytes = device_len(fs) - fs.bytes_per_cluster

    clusters = list()

    for i in range(len(fs.fat)):
        if i < min_valid_cluster or i > max_valid_cluster:
            continue

        if fs.get_data_cluster_address(i) >= device_bytes:
            break

        if fs.fat[i] == free_cluster_value:
            if i == bad_cluster_value:
                continue
            if fs.fat_type == fs.FAT_TYPE_FAT12 and i == fs.FAT12_SPECIAL_EOC:
                continue

            clusters.append(i)

    if offset < 0:
        clusters = clusters[::-1]

    if abs(offset) > 1:
        clusters = clusters[abs(offset)-1:]
        
    return clusters


def read_slug(fs, clusters, free_clusters_list):
    slug_bytes = b"".join([read_cluster(fs, cluster) for cluster in free_clusters_list[:clusters]])
    return slug_bytes


def write_slug(fs, free_clusters_list, slug_bytes):
    blocks = [slug_bytes[i:i + fs.bytes_per_cluster] for i in range(0, len(slug_bytes), fs.bytes_per_cluster)]
    for i in range(len(blocks)):
        # print(f"Writing cluster to {free_clusters_list[i]}, {type(blocks[i])=}", file=sys.stderr)
        write_cluster(fs, free_clusters_list[i], blocks[i])


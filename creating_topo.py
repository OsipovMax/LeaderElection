import random
from process import Process


def creat_ring_topo(node_count: int) -> list:
    lst_id = [x for x in range(node_count)]
    random.shuffle(lst_id)
    print(lst_id)
    ring_topo = []
    for index, proc_id in enumerate(lst_id[: node_count - 1]):
        tmp_proc = Process(proc_id, node_count - 1)
        tmp_proc.prev_nb = lst_id[index - 1]
        tmp_proc.next_nb = lst_id[index + 1]
        ring_topo.append(tmp_proc)
    tmp_proc = Process(lst_id[node_count - 1], node_count - 1)
    tmp_proc.prev_nb = lst_id[node_count - 2]
    tmp_proc.next_nb = lst_id[0]
    ring_topo.append(tmp_proc)
    return ring_topo

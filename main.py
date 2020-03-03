import pika
import time
import threading
from process import Process
from creating_topo import creat_ring_topo

# Number of processes in a distributed system
process_count = 7
# numer of circle on normal work (without drop)
num_work_circle = 1
# glob var for modeling distributed work
mutex = threading.Lock()
shared_variable = 0
   
def process_work(process: Process) -> None:
    global shared_variable
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    standard_work = True
    while len(process.topology) > 2:
        # normal work of distributed system 
        if standard_work:
            mutex.acquire()
            if shared_variable == process_count * num_work_circle:
                #normal work in the distributed system is finished
                standard_work = False
            else:
                shared_variable += 1
            mutex.release()
        if process.process_id == process.leader_id and standard_work == False:
            print("i am a process with ID = {0} and failed.".format(process.process_id))
            connection.close()
            return None
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = process.send_message(connection, str(process.next_nb), "I am process with ID = {0}, and I'm your neighbor.".format(process.process_id)) 
        process.recv_message(connection, channel, str(process.process_id))
    connection.close()

if __name__ == "__main__":
    threads = [] 
    topo = creat_ring_topo(process_count)
    print(topo)
    for process in topo:
        process.topology = [x.process_id for x in topo]
        trd = threading.Thread(target=process_work, args=(process,))
        threads.append(trd)
        trd.start()
    for tread in threads:
        tread.join()
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    for i in range(process_count):
        channel.queue_purge(queue=str(i))
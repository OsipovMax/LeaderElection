class Process:
    def __init__(self, process_id, leader_id):
        self.process_id = process_id
        self.leader_id = leader_id
        self.prev_nb = 0
        self.next_nb = 0
        self.topology = []
        self.election_buffer = []
        self.is_initiator_election = False

    def send_message(self, conn, queue_title, text_message):
        channel = conn.channel()
        channel.queue_declare(queue = queue_title)
        channel.basic_publish(exchange = '', routing_key = queue_title, body = text_message)
        return channel

    def init_election(self, conn, queue_title, channel):
        print("Running election.")
        new_prev_nb_ind = self.topology.index(self.leader_id) - 1
        if new_prev_nb_ind == -1:
            new_prev_nb_ind = len(self.topology) - 1
        self.prev_nb = self.topology[new_prev_nb_ind]
        self.send_message(conn, str(self.next_nb), "Election")
        self.is_initiator_election = True
        self.leader_election(conn, channel, queue_title)

    def accept_elections(self, conn, queue_title, channel):
        if self.next_nb == self.leader_id:
            new_next_nb_ind = self.topology.index(self.leader_id) + 1
            if new_next_nb_ind == len(self.topology):
                new_next_nb_ind = 0
            self.next_nb = self.topology[new_next_nb_ind]
            self.leader_election(conn, channel, queue_title)
            return None
        self.send_message(conn, str(self.next_nb), "Election")
        self.leader_election(conn, channel, queue_title)

    def recv_message(self, conn, channel, queue_title):
        for _, _, body in channel.consume(queue = queue_title, auto_ack = True, inactivity_timeout = 3):
            if body is not None:
                print("I am a process with ID = {0}. I got a message : {1}".format(self.process_id,body.decode('utf-8')))
            else:
                print("I am a process with ID = {0}. The message is not received (timeout)".format(self.process_id))

            if self.prev_nb == self.leader_id:
                if body is not None:
                    self.send_message(conn, str(self.next_nb), "Ok")
                else:
                    self.init_election(conn, queue_title, channel)
                    return None
            elif self.process_id != self.leader_id:
                for _, _, body in channel.consume(queue = queue_title, auto_ack = True, inactivity_timeout = 3):
                    if body == b"Ok":
                        channel.cancel()
                    elif body == b"Election":
                        self.accept_elections(conn, queue_title, channel)
                        return None
                if self.next_nb != self.leader_id:
                    self.send_message(conn, str(self.next_nb), "Ok")
            channel.cancel()
        channel.close()

    def leader_election(self, conn, channel, queue_title):
        tmp_buf = []
        self.topology.remove(self.leader_id)
        if self.is_initiator_election:
            print("I am initiator of election and I propose my candidacy, my id = {0}.".format(self.process_id))
            self.election_buffer.append(self.process_id)
            self.send_message(conn, str(self.next_nb), bytes(self.election_buffer))
            for _, _, body in channel.consume(queue = queue_title, auto_ack = True, inactivity_timeout = 3):
                tmp_buf = list(body)
                self.election_buffer = tmp_buf
                channel.cancel()
            print("OK, I have collected all the candidates, and now I will choose the best one.")
            new_leader = max(self.election_buffer)
            print("Leader it is a process with id = {0}.".format(new_leader))
            self.send_message(conn, str(self.next_nb), str(new_leader))
            self.leader_id = new_leader
            self.is_initiator_election = False
            for _, _, body in channel.consume(queue = queue_title, auto_ack = True, inactivity_timeout = 3):
                print("OK, the leader is updated for all processes.")
                channel.cancel()
        else:
            for _, _, body in channel.consume(queue = queue_title, auto_ack = True, inactivity_timeout = 3):
                tmp_buf = list(body)
                self.election_buffer = tmp_buf
                print("I also propose my candidacy, my id = {0}".format(self.process_id))
                self.election_buffer.append(self.process_id)
                channel.cancel()
            self.send_message(conn, str(self.next_nb), bytes(self.election_buffer))
            for _, _, body in channel.consume(queue = queue_title, auto_ack = True, inactivity_timeout = 3):
                self.leader_id = int(body.decode('utf-8'))
                channel.cancel()
            self.send_message(conn, str(self.next_nb), str(self.leader_id))
        self.election_buffer = []
        
    def __repr__(self):
        return "Process id = {0}, Prev nb = {1}, Next nb = {2}".format(self.process_id, self.prev_nb, self.next_nb)

from simulator.node import Node
import json
import heapq
from collections import defaultdict


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # self.neighbors is defined inside the Node class in simulator/Node.py
        self.world_representation = defaultdict(lambda: defaultdict(int)) # { id1: {id2: cost}, ...}
        self.seen = {} # { neighbor: max_sequence_seen_as_int }
        self.sequence_number = 0

    # Return a string
    def __str__(self):
        """
        Prints represenation of node state for debugging purposes,
        not strictly necessary to implement but helpful

        Parameters:
        None

        Returns:
        state (str): representation of node state

        """
        dump = f"Node {self.id} graph: {self.world_representation}"
        return dump


    # Called to inform Node that outgoing link properties have changed
    def link_has_been_updated(self, neighbor, latency):
        """
        Updates node tables with new latency to reach neighbor,
        and forwards this update to node's neighbors.

        Parameters:
        neighbor (Node): neighbor sending the update
        latency (float): new latency to reach neighbor

        Returns:
        None
        """
        print("link_has_been_updated: ", self.id, neighbor, latency)

        # If Latency is -1 delete
        if latency == -1:
            # Update local representation to delete the node completely. 
            # Send the message with latency -1 to all neighbors. And they should also just delete it. 
            if self.id in self.world_representation and neighbor in self.world_representation[self.id]:
                self.world_representation[self.id][neighbor] = latency
            
            if neighbor in self.world_representation and self.id in self.world_representation[neighbor]:
                self.world_representation[neighbor][self.id] = latency

            self.sequence_number += 1
            message = {
                'source': self.id,
                'destination': neighbor,
                'seq': self.sequence_number,
                'cost': latency,
                'neighbors_representation_of_the_world': self.world_representation
            }

            # Flooding
            self.send_to_neighbors(json.dumps(message))



        else:
            # print(f"UPDATE BETWEEN {self.id} AND {neighbor} = {latency}")
            self.world_representation[self.id][neighbor] = latency
            self.world_representation[neighbor][self.id] = latency

            # Update neighbors on new representation of the world
            self.sequence_number += 1
            message = {
                'source': self.id,
                'destination': neighbor,
                'seq': self.sequence_number,
                'cost': latency,
                'neighbors_representation_of_the_world': self.world_representation
            }

            # Flooding
            self.send_to_neighbors(json.dumps(message))


    def process_incoming_routing_message(self, m):
        """
        Choose course of action for message, sending message to
        neighbor(s) and/or updating tables

        Parameters:
        m (str): routing message

        Returns:
        None

        """

        message = json.loads(m)
        source = message['source']
        destination = message['destination']
        seq = message['seq']
        cost = message['cost']
        neighbors_representation_of_the_world = message['neighbors_representation_of_the_world']


        # If the source has been seen before, then check its set of sequence numbers
        if source in self.seen:

            # If the sequence number has been seen, or the sequence number is less than the max -----> do nothing
            if seq <= self.seen[source]:
                return
            
            # Handling a deletion
            if cost == -1:
                if source in self.world_representation and destination in self.world_representation[source]:
                    del self.world_representation[source][destination]
                    self.send_to_neighbors(m)
                    
            else:                
                # Add it to the seen set
                self.seen[source] = seq
                
                # Otherwise this is new. Let's update my own representation and forward this to all neighbors
                self.world_representation[source][destination] = cost
                self.world_representation[destination][source] = cost

                # Flooding to neighbors
                self.send_to_neighbors(m)

        else:
            # Otherwise source has never been seen, so it is the first time we have heard of it... New. 
            # print("Entered the new portion")
            self.seen[source] = seq

            # Update world representation
            self.world_representation[source][destination] = cost
            self.world_representation[destination][source] = cost

            # If I am a brand new node, I might be missing information. Update that, too. 
            self.update_global_info(neighbors_representation_of_the_world)

            # Flooding to neighbors
            self.send_to_neighbors(m)


    def update_global_info(self, neighbor_representation):
        """Helper function that handles sharing information from a more knowledgeable node to a lesser one. 
        
        """
        for neighbor_source, neighbor_adj in neighbor_representation.items():
            neighbor_source = int(neighbor_source)

            # If my neighbor has a source that I don't have. I should add that entire representation to my own
            if neighbor_source not in self.world_representation:
                self.world_representation[neighbor_source] = defaultdict(int)

            for dest, cost in neighbor_adj.items():
                dest = int(dest)
                if dest not in self.world_representation[neighbor_source]:
                    self.world_representation[neighbor_source][dest] = cost
         
        
    def get_next_hop(self, destination):
        """
        Node is asked which hop it THINKS is next on path to destination

        Parameters:
        destination (Node): final destination being searched for

        Returns:
        hops (int): next Node to reach destination

        """
        dist, prev = self.dijkstra(destination)
        path = []
        u = destination
        source = self.id

        while u is not None:
            path.append(u)
            u = prev[u]

        if path[-1] == source:
            path.reverse()
            return path[1]
        else:
            return -1

        # https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
        # 1  S ← empty sequence
        # 2  u ← target
        # 3  if prev[u] is defined or u = source:          // Proceed if the vertex is reachable
        # 4      while u is defined:                       // Construct the shortest path with a stack S
        # 5          insert u at the beginning of S        // Push the vertex onto the stack
        # 6          u ← prev[u]                           // Traverse from target to source

    def dijkstra(self, destination):
        '''
        Dijkstra's Shortest Path Algorithm

        self.graph =
        {
            0: {2: 2, 1: 2, 3: 100},
            1: {0: 2, 2: 50},
            2: {0: 2, 1: 50},
            3: {0: 100}
        }

        self.graph[source][dest] = latency
        '''
        source = self.id
        n_prime = set()
        dist = {}
        prev = {}
        q = []

        # Initialization:
        for vertex in self.world_representation.keys():
            if vertex == source:
                dist[vertex] = 0
            else:
                dist[vertex] = float('inf')
            prev[vertex] = None
    
            heapq.heappush(q, (dist[vertex], vertex))

        # Loop - until N prime = N
        while q:
            _, w_vector = heapq.heappop(q)

            if w_vector in n_prime:
                continue
            n_prime.add(w_vector)

            for neighbor_v, weight in self.world_representation[w_vector].items():
                if neighbor_v in n_prime:
                    continue

                new_distance = dist[w_vector] + weight
                if new_distance < dist[neighbor_v]:
                    dist[neighbor_v] = new_distance
                    prev[neighbor_v] = w_vector
                    heapq.heappush(q, (new_distance, neighbor_v))

        return dist, prev
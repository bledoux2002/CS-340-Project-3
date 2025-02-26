from simulator.node import Node
import json
import heapq


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.neighbor_dict = {}
        self.graph = {}
        self.sequence_number = 0
        self.messages = {}

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
        return "Rewrite this function to define your node dump printout"

    def update_graph(self, source_id, neighbor_to_update, new_latency):
        pass

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

        # step 1: latency = -1 if delete a link
        if latency == -1:
            print("COME BACK AND HANDLE THIS DELETION")
            return
            
        # print(f"Link updated between {self.id} and {neighbor} to latency {latency}")

        # step 2: Update neighbors with new latency to neighbor
        # Link updated between 1 and 2 to latency 2
        # {0: 2, 2: 2}
        self.neighbor_dict[neighbor] = latency

        if self.id not in self.graph: 
            self.graph[self.id] = {}
        self.graph[self.id][neighbor] = latency

        if neighbor not in self.graph:
            self.graph[neighbor] = {}
        self.graph[neighbor][self.id] = latency

        print(f"Link updated between {self.id} and {neighbor}. Graph = {self.graph}")
        
        self.sequence_number += 1
        message = json.dumps({
            'source': self.id,
            'dest': neighbor,
            'cost': latency,
            'sender': self.id,
            'seq': self.sequence_number
        })
        

        for neigh in self.neighbor_dict.keys():
            if neigh != neighbor:
                self.send_to_neighbor(neigh, message)
        
    
    def process_incoming_routing_message(self, m):
        """
        Choose course of action for message, sending message to
        neighbor(s) and/or updating tables

        Parameters:
        m (str): routing message

        Returns:
        None

        Link updated between 2 and 0. Graph = {2: {0: 2}, 0: {2: 2}}
        Link updated between 0 and 2. Graph = {0: {2: 2}, 2: {0: 2}}
        Link updated between 2 and 1. Graph = {2: {0: 2, 1: 2}, 0: {2: 2}, 1: {2: 2}}
        Link updated between 0 and 1. Graph = {0: {2: 2, 1: 2}, 2: {0: 2}, 1: {0: 2}}
        Link updated between 1 and 0. Graph = {1: {0: 2}, 0: {1: 2}}
        Link updated between 1 and 2. Graph = {1: {0: 2, 2: 2}, 0: {1: 2}, 2: {1: 2}}
        [2025-02-26 17:08:53][INFO] Sim: Time: 2, Comment: "Done"
        incoming routing message

        NODE 2 has an internal representation as: {2: {0: 2, 1: 2}, 0: {2: 2}, 1: {2: 2}}
        Message updating source 0  dest 1  seq: 1
        
        """
        print("incoming routing message")
        print(f"NODE {self.id} has an internal representation as: {self.graph}")

        message = json.loads(m)
        source = message['source']
        dest = message['dest']
        cost = message['cost']
        sender = message['sender'] # this will not be consistent across network for each node's self.last_message, sholdnt need to be
        seq = message['seq']
        print(f"Message updating source {source}  dest {dest}  seq: {seq}  sequence_number: {self.sequence_number}")

        if seq >= self.sequence_number + 1:
            # update table and forward
            message['sender'] = self.id
            self.messages[seq] = message
            if source not in self.graph:
                self.graph[source] = {} 
            if dest not in self.graph:
                self.graph[dest] = {}
            self.graph[source][dest] = cost 
            self.graph[dest][source] = cost
            
            # seq could be part of bringing outdated node up to speed
            if seq > self.sequence_number + 1:
                # graph too outdated, send last message back (will receive next message in order, will continue until no longer outdated)
                self.send_to_neighbor(sender, json.dumps(self.messages[self.sequence_number]))
            elif seq < max(self.messages): # case where node being updated, check if self.seq is same as largest in messages or still needs to be updated
                self.sequence_number += 1
                self.send_to_neighbor(sender, json.dumps(self.messages[self.sequence_number]))
            else:
                # graph up to date, now we can flood and update our sequence num (already in messages, up to date graph may have been overwritten from "catch up" steps so redundancy necessary)
                self.sequence_number += 1
                for neigh in self.neighbor_dict.keys():
                    if neigh != sender:
                        self.send_to_neighbor(neigh, json.dumps(message))

        elif seq < self.sequence_number:
            # send next sequence following received sequence back (updates table for out of date node)
            if seq + 1 in self.messages:
                self.send_to_neighbor(sender, json.dumps(self.messages[seq + 1]))
            else:
                # Handle the case where the next sequence isn't available
                # Maybe send the latest message you have or log an error
                print(f"node {self.id}")
                latest_available = max(self.messages.keys())
                self.send_to_neighbor(sender, json.dumps(self.messages[latest_available]))
     


    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        """
        Node is asked which hop it THINKS is next on path to destination
        
        Parameters:
        destination (Node): final destination being searched for
        
        Returns:
        hops (int): next Node to reach destination
        
        """
        # step 1: determine next node to destination from table?
        _, _, path = self.dijkstra(destination)

        print(f"PATH FROM {self.id} --> {destination} is == {path}")
        

        if len(path) < 2:
            return -1
        return path[1] # PATH FROM 1 --> 3 is == [1, 0, 3] So therefore our next hop is the first index
    
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
        q = []
        dist = {}
        prev = {}

        for vertex in self.graph.keys():
            dist[vertex] = float('inf')
            prev[vertex] = None
            heapq.heappush(q, (dist[vertex], vertex))  # (Distance, vertex)
        
        dist[source] = 0
        heapq.heappush(q, (dist[source], source)) 

        while q:
            curr_dist, u = heapq.heappop(q)

            if curr_dist > dist[u]:
                continue

            for neighbor_v, latency in self.graph[u].items():
                alt = dist[u] + latency
                if alt < dist[neighbor_v]:
                    dist[neighbor_v] = alt
                    prev[neighbor_v] = u
                    heapq.heappush(q, (dist[neighbor_v], neighbor_v))

        path = []
        u = destination
        while u is not None or u == source:
            path.append(u)
            u = prev[u]
        
        path.reverse()

        return dist, prev, path

                
    
# Wikipedia has always had my favorite pseudocode for Dijkstra's so I based it off of this:
# https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
#  1  function Dijkstra(Graph, source):
#  2     
#  3      for each vertex v in Graph.Vertices:
#  4          dist[v] ← INFINITY
#  5          prev[v] ← UNDEFINED
#  6          add v to Q
#  7      dist[source] ← 0
#  8     
#  9      while Q is not empty:
# 10          u ← vertex in Q with minimum dist[u]
# 11          remove u from Q
# 12         
# 13          for each neighbor v of u still in Q:
# 14              alt ← dist[u] + Graph.Edges(u, v)
# 15              if alt < dist[v]:
# 16                  dist[v] ← alt
# 17                  prev[v] ← u
# 18
# 19      return dist[], prev[]
    
# 1  S ← empty sequence
# 2  u ← target
# 3  if prev[u] is defined or u = source:          // Proceed if the vertex is reachable
# 4      while u is defined:                       // Construct the shortest path with a stack S
# 5          insert u at the beginning of S        // Push the vertex onto the stack
# 6          u ← prev[u]                           // Traverse from target to source
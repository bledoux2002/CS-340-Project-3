from simulator.node import Node
import json
import heapq


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # self.neighbors is defined inside the Node class in simulator/Node.py
        self.neighbors_dict = {}
        self.graph = {}
        self.seq_num_tracker = {}
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
        return "Rewrite this function to define your node dump printout"
    
    def update_graph(self, source, neighbor, latency):
        '''Bidirectionally updates our graph representation of the world'''
        source, neighbor, latency = int(source), int(neighbor), int(latency)

        if source not in self.graph:
            self.graph[source] = {}
        if neighbor not in self.graph:
            self.graph[neighbor] = {}
        self.graph[source][neighbor] = latency
        self.graph[neighbor][source] = latency

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
            print("COME BACK AND HANDLE THIS")
            return
            
        # step 2: Update neighbors with new latency to neighbor

        # Updating neighbors
        if neighbor not in self.neighbors_dict:
            self.neighbors_dict[neighbor] = {}
        self.neighbors_dict[neighbor] = latency

        # Updating internal graph representation
        self.update_graph(self.id, neighbor, latency)

        # Create Link State Advertisement of my newly updated neighbors
        self.sequence_number += 1
        message = {
            'source': self.id,
            'seq': self.sequence_number,
            'new_neighbors': self.neighbors_dict,
            'previous_router': self.id
        }

        # Flooding
        for neigh in self.neighbors_dict.keys():
            if neigh != neighbor:
                self.send_to_neighbor(neigh, json.dumps(message))


      

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
        seq = message['seq']
        new_neighbors = message['new_neighbors']
        previous_router = message['previous_router']

        if source not in self.seq_num_tracker or seq > self.seq_num_tracker[source]:
            self.seq_num_tracker[source] = seq

            # Accepting and updating our internal graph of the world
            for updated_neighbor, updated_latency in new_neighbors.items():
                self.update_graph(source, updated_neighbor, updated_latency)

            # Flooding
            message['previous_router'] = self.id # Updating the previous router to the current router
            for neigh in new_neighbors.keys():
                if neigh != previous_router:
                    self.send_to_neighbor(neigh, json.dumps(message))
            
        else:
            print("Already seen sequence number...")
            pass


            

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
        print(f"NODE: {self.id} INTERNAL REP: {self.graph}")
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
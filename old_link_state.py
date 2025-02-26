from simulator.node import Node
import json
import heapq


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # self.neighbors is defined inside the Node class in simulator/Node.py
        self.graph = {}
        self.seq_num_tracker = {}
        self.sequence_number = 0
        self.UPDATE_GRAPH_FLAG = 999

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
        """
        ## Description
        -----------
        Updates the global network graph of routers to reflect the 
        most up-to-date latency.

        ## Parameters
        ----------
        source_id: Source ID 
        neighbor_to_update: The pair between source-neighbor that we are updating
        new_latency: The cost between source and neighbor
        """
        if source_id in self.graph:
            self.graph[source_id][neighbor_to_update] = new_latency
        else:
            self.graph[source_id] = {}
            self.graph[source_id][neighbor_to_update] = new_latency

        print(f"Updated latency between {source_id} and {neighbor_to_update} to ~{new_latency}~ inside of node {self.id}")
        # print(self.graph)


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
        # Update our local neighbor mapping.

        found = False
        for index, (neigh, _) in enumerate(self.neighbors):
            if neigh == neighbor:
                found = True
                self.neighbors[index] = (neighbor, latency)
        if not found:
            self.neighbors.append((neighbor, latency))


        self.update_graph(self.id, neighbor, latency)
        self.update_graph(neighbor, self.id, latency)

        """
        NOTE:
        Just because our local mapping is up to date, doesn't mean other's are. 
        So we will not "flood" where other routers in the AS will update the source link
        such that the neighbor of this source link on the other system's end will reflect the new 
        latency. 

        For example, if the connection between source node 1 and 3 changes to latency 100. Then 
        we would send out:

            source: 1
            neighbor_to_update: 3
            latency: 100

        The next system that receives this message (inside of process_incoming_routing_message), and verifies that it is "new", 
        can update their internal record so that it reflects something along the lines of:

            {
                0: [ (neighbor 1, latency), ... (neighbor 3, 100), ...],
                ...
                ...
            }

        This can be thought of as a new router doing:

            self.graph[source][neighbor_to_update] = new_latency
        """    

        self.sequence_number += 1

        source_id = self.id
        seq_num = self.sequence_number
        neighbor_to_update = neighbor
        new_latency = latency
        message = json.dumps({
            'source_id': source_id,
            'seq_num': seq_num,
            'neighbor_to_update': neighbor_to_update,
            'new_latency': new_latency
        })

        for neigh, _ in self.neighbors:
            # If it is not the neighbor that already updated the link, we flood
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
        
        """

        """
        NOTE:
        Ok you found my next comment on this mission. Think of this function as a separate router 
        receiving a "flood" request. Therefore, another system is attempting to tell us to update our internal
        records about a change in latency. 

        We are receiving a source, sequence number, neighbor to update, and a new latency. 

        Things to check:
            1) If the source id exists
                2a) If the source id exists, then we can just update it easily as self.graph[source][neighbor] = latency
                2b) If the source id doesn't exist yet, then we need to set self.graph[source] = {}
                    2A) Now that it has a dict inside of a dict we can do the same logic as 2a and set the latency. 

        """

        # If it is a dictionary we are telling it to hard reset its internal representation
        if isinstance(m, dict):
            self.graph = m
            print(f"Updated view of the world. NODE {self.id} is {self.graph}")
            return
        
        # Otherwise it is of type JSON, so we process like normal
        if isinstance(m, str):
            message = json.loads(m)
            source_id = message['source_id']
            seq_num = message['seq_num']
            neighbor_to_update = message['neighbor_to_update']
            new_latency = message['new_latency']
            
            # Bidirectional undirected graph
            self.update_graph(source_id, neighbor_to_update, new_latency)
            self.update_graph(neighbor_to_update, source_id, new_latency)

            # Controlled flooding 
            new_connection = False
            if source_id not in self.seq_num_tracker:
                self.seq_num_tracker[source_id] = {}
                self.seq_num_tracker[source_id][seq_num] = True
                new_connection = True


            elif seq_num not in self.seq_num_tracker[source_id]:
                # Sequence number not seen yet for this source
                self.seq_num_tracker[source_id][seq_num] = True  
                for neigh, _ in self.neighbors:
                    if neigh != neighbor_to_update:
                        self.send_to_neighbor(neigh, m)

            # If it is a brand new connection, it needs a updated view of the world
            if new_connection:
                self.send_to_neighbor(neighbor_to_update, self.graph)

            print(f"Updated view of the world. NODE {self.id} is {self.graph}")
            

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
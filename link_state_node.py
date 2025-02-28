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
        dump = f"Node {self.id} graph: {self.graph}"
        return dump
    
    def update_graph(self, source, neighbor, latency):
        '''Bidirectionally updates our graph representation of the world'''
        source, neighbor, latency = int(source), int(neighbor), int(latency)
        
        '''
        What was deleted
        ----------------
        Node 1 was deleted


        Deleted information
        -------------------
        Deletion inside of node: 2
        Before (neighbors): {0: 2, 1: 50}
        After (neighbors): {0: 2}

        Updating the graph 
        ------------------            
        Graph before:  {2: {0: 2, 1: 50}, 0: {2: 2, 1: 2, 3: 4}, 1: {2: 50, 0: 2}, 3: {0: 4}}
        Graph after:  {2: {0: 2}, 0: {2: 2, 3: 4}, 3: {0: 4}}
        '''

        if latency == -1:
            # DELETE_LINK
            # print(f"A DELETION ARRIVED AT NODE {self.id} TO DELETE LINK {source} {neighbor}")
            # print("Graph before: ", self.graph)
            if source in self.graph:
                # Check if source in graph, and if neighbor connected to source
                # should only have to check source to neighbor, not vice versa because that will come from neighbor as source later?
                if neighbor in self.graph[source]:
                    del self.graph[source][neighbor] # Completely deleting the node
            
                # DELETE_NODE
                if not self.graph[source]:
                    # All links to source have been deleted, so now we know it was a "DELETE_NODE" command, and to remove it from our graph
                    del self.graph[source]

            # print("Graph after: ", self.graph)
        else:
            if source not in self.graph:
                self.graph[source] = {}
            self.graph[source][neighbor] = latency


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

        # If latency is -1 we delete the link from our neighbors list. Otherwise we update our neighbor list
        if latency == -1:
            print(f"Deletion inside of node: {self.id}")
            print(f"Before (neighbors): {self.neighbors_dict}")
            if neighbor in self.neighbors_dict:
                del self.neighbors_dict[neighbor]
            print(f"After (neighbors): {self.neighbors_dict}")
        else:
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
        seq = message['seq']
        new_neighbors = message['new_neighbors']
        previous_router = message['previous_router']

        if source not in self.seq_num_tracker or seq > self.seq_num_tracker[source]:
            self.seq_num_tracker[source] = seq

            # Accepting and updating our internal graph of the world
            # print(f"Graph of node {self.id} before: {self.graph}")
            for updated_neighbor, updated_latency in new_neighbors.items():
                self.update_graph(source, updated_neighbor, updated_latency)
            # print(f"Graph of node {self.id} after: {self.graph}")

            # Flooding
            message['previous_router'] = self.id # Updating the previous router to the current router
            self.send_to_neighbors(json.dumps(message))
            
        else:
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
        dist, prev = self.dijkstra(destination)
        path = []
        u = destination
        source = self.id

        while u is not None:
            path.append(u)
            u = prev[u]
            
        print(self.graph)
        print(f"PATH {source} to {destination} is: {path}")
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
        for vertex in self.graph.keys():
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
            
            for neighbor_v, weight in self.graph[w_vector].items():
                if neighbor_v in n_prime:
                    continue 
                
                new_distance = dist[w_vector] + weight
                if new_distance < dist[neighbor_v]:
                    dist[neighbor_v] = new_distance
                    prev[neighbor_v] = w_vector  
                    heapq.heappush(q, (new_distance, neighbor_v)) 
        
        return dist, prev

                
    

from simulator.node import Node
import json
import copy

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.neighbors_dict = {} # cost from self.id to neighbor is latency {1 : 2, ...} If we are node 0 it takes cost 2 to reach 1
        self.distance_vector = {} # {all destinations: (cost, [path of least cost to dest])   
        self.neighbors_dv = {} # distance_vectors of all neighbors

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
        # step 1: Update Tables w/ new latency to reach neighbor
        # latency = -1 if delete a link
        if latency == -1:
            del self.neighbors_dict[neighbor]
            del self.neighbors_dv[neighbor]

        else:
            # step 2: Update neighbors with new latency to neighbor
            self.neighbors_dict[neighbor] = latency
            self.distance_vector[neighbor] = (latency, [neighbor]) # (cost, least cost path to dest) add path
        
        if self.__calculate_dv():
            # DV has changed, forward to neighbors
            print("Flooding")
            message = {
                'source': self.id,
                'distance_vector': self.distance_vector
            }
            self.send_to_neighbors(json.dumps(message))


    # Fill in this function
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
        source = message['source'] # Where it came from (our neighbor)
        new_dv = message['distance_vector']

        # Saving our neighbors distance vector 
        self.neighbors_dv[source] = new_dv

        # Updating our own distance vector using Bellman-Ford
        if self.__calculate_dv():
            # DV has changed, forward to neighbors
            print("Flooding")
            message = {
                'source': self.id,
                'distance_vector': self.distance_vector
            }
            self.send_to_neighbors(json.dumps(message))
        
      

        # step 1: interpret message


        # step 2: choose course of action

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
        print("NEXT HOP")
        print(destination)
        print(self.distance_vector)
        print()
        print()
        print()

        hops = -1
        return hops


    # Take our DV and our neighbors_DV and recalculate our DV from scratch, forward to neighbors if different (assuming something changed)
    def __calculate_dv(self):
        old_neighbors = copy.deepcopy(self.neighbors_dict)
        old_dv = copy.deepcopy(self.distance_vector)
        print(f"NODE {self.id}")
        print(f"Neighbors Dict {self.neighbors_dict}")
        print(f"Distance Vector {self.distance_vector}")

        dist, prev = self.__bellman_ford()
        self.distance_vector = dist

        if self.neighbors_dict != old_neighbors or self.distance_vector != old_dv:
            return 1
        return 0
    

    def __bellman_ford(self):
        # Initialization
        dist = {vertex: float('inf') for vertex in self.distance_vector.keys()}
        prev = {vertex: None for vertex in self.distance_vector.keys()}
        dist[self.id] = 0  # Distance to the source is 0

        # Relax all edges V-1 times
        for _ in range(len(self.distance_vector) - 1):
            for u in self.distance_vector:
                for v, cost in self.neighbors_dv.get(u, {}).items():  # Assuming neighbors_dv holds neighbors and costs
                    alt_cost = dist[u] + cost  # cost should be the weight between u and v
                    if alt_cost < dist[v]:
                        dist[v] = alt_cost
                        prev[v] = u

        # Check for negative weight cycles
        for u in self.distance_vector:
            for v, cost in self.neighbors_dv.get(u, {}).items():
                if dist[u] + cost < dist[v]:
                    print("Graph contains a negative weight cycle")
                    return None, None

        print(f"dist {dist}")
        return dist, prev


    def __bellman_ford_ben(self):
        # Initialization
        dist = {}
        prev = {}

        for vertex in self.distance_vector.keys():
            dist[vertex] = float('inf')
            prev[vertex] = None
        dist[self.id] = 0
        # prev[self.id] = [self.id] # full path, try only one for now and deal with infinite loops later

        # Relax edges 
        for _ in range(len(self.distance_vector) - 1):
            #for each edge (u, v):
                #alt = dist[u] + (u, v).cost
                #if alt < dist[v]:
                    #dist[v] = alt
                    #prev[v] = u # change for full path?
        
        
            for neighbor, path in self.neighbors_dv.items():
                u = self.id
                v = neighbor
                alt = dist[u] + cost

                if alt < dist[v]:
                    dist[v] = alt       
                    prev[v] = prev[u] + [v]

        # Outputs are distance and predecessor arrays
        print(f"dist {dist}")
        print(f"prev {prev}")
        return dist, prev
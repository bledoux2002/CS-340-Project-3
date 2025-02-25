from simulator.node import Node
import json


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.neighbors = {}
        self.forwarding_table = {}

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
        
        # step 1: latency = -1 if delete a link
        if latency == -1 and neighbor in self.neighbors:
            del self.neighbors[neighbor]
            return
                
        self.neighbors[neighbor] = latency
        print(f"I am node: {self.id} and my neighbors are {self.neighbors}")
        
        # step 2: Update neighbors with new latency to neighbor
        message = {
            'source': self.id,
            'neighbors': self.neighbors
        }

        # Broadcasting new info to neighbors
        for n in self.neighbors:
            if n != neighbor:
                self.send_to_neighbor(n, json.dumps(message))

        

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
        neighbors = message['neighbors']
        
        # Need to update the latency on our end
        for neighbor, latency in neighbors.items():
            if (neighbor, latency) not in self.neighbors:
                self.neighbors[neighbor] = latency
                print("A neighbor's latency was updated.")
            
        # HERE IS WHERE WE NEED TO RUN DIJKSTRA'S TO FINALLY UPDATE THE 
        # self.forwarding_table INFORMATION


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
        print("WANTS NEXT HOP")

        hops = -1
        return hops
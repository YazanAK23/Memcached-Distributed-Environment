import logging
import hashlib
from pymemcache.client.base import Client
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


nodes = {
    "node1": Client(("localhost", 11211)),
    "node2": Client(("localhost", 11212)),
    "node3": Client(("localhost", 11213))
}


REPLICATION_FACTOR = 2


class HashRing:
    def __init__(self, nodes):
        self.nodes = nodes
        self.ring = self.build_ring()

    def build_ring(self):
        ring = {}
        for node in self.nodes:
            node_hash = hashlib.md5(node.encode()).hexdigest()
            ring[node_hash] = node
        return ring

    def get_node(self, key):
        key_hash = hashlib.md5(key.encode()).hexdigest()
        sorted_hashes = sorted(self.ring.keys())
        for node_hash in sorted_hashes:
            if key_hash <= node_hash:
                return self.ring[node_hash]
        return self.ring[sorted_hashes[0]]

    def get_nodes(self, key, replication_factor):
        primary_node = self.get_node(key)
        sorted_nodes = sorted(self.ring.keys())
        primary_index = sorted_nodes.index(hashlib.md5(primary_node.encode()).hexdigest())
        replicas = [self.ring[sorted_nodes[(primary_index + i) % len(sorted_nodes)]]
                    for i in range(replication_factor)]
        return replicas


ring = HashRing(nodes.keys())


def set_data(key, value):
    try:
        primary_node = ring.get_node(key)
        replica_nodes = ring.get_nodes(key, REPLICATION_FACTOR)
        
        # Set the data on the primary node and replica nodes
        for node_name in {primary_node, *replica_nodes}:
            if node_name in nodes:
                client = nodes[node_name]
                client.set(key, value)
                logging.info(f"Data set on {node_name}: {key} -> {value}")
            else:
                logging.warning(f"Node {node_name} is not available.")
        
      
        log_data_distribution(key)

    except Exception as e:
        logging.error(f"Failed to set data on nodes for key: {key}. Error: {e}")


def log_data_distribution(key):
    logging.info("Current data distribution across nodes:")
    for node_name in nodes:
        client = nodes[node_name]
        value = client.get(key)
        if value is not None:
            logging.info(f"Key: {key} is stored on {node_name}")


def get_data(key):
    primary_node = ring.get_node(key)
    replica_nodes = ring.get_nodes(key, REPLICATION_FACTOR)
    
    for node_name in [primary_node, *replica_nodes]:
        try:
            if node_name in nodes:
                client = nodes[node_name]
                value = client.get(key)
                if value is not None:
                    logging.info(f"Data retrieved from {node_name}: {key} -> {value.decode()}")
                    return value
                else:
                    logging.warning(f"No data found on {node_name} for key: {key}")
        except Exception as e:
            logging.warning(f"Failed to retrieve data from {node_name} for key: {key}. Trying next node. Error: {e}")
    
    logging.error(f"Cache miss for key: {key}. Data not found in any replica nodes.")
    return None


def delete_data(key):
    try:
        primary_node = ring.get_node(key)
        replica_nodes = ring.get_nodes(key, REPLICATION_FACTOR)

        for node_name in {primary_node, *replica_nodes}:
            if node_name in nodes:
                client = nodes[node_name]
                if client.get(key) is not None:
                    client.delete(key)
                    logging.info(f"Data deleted from {node_name}: {key}")
                else:
                    logging.warning(f"Key {key} not found on {node_name} for deletion.")
            else:
                logging.warning(f"Node {node_name} is not available.")
    except Exception as e:
        logging.error(f"Failed to delete data on nodes for key: {key}. Error: {e}")


def manual_failover_test():

    set_data("111", "Users")
    set_data("222", "Products")
    
    
    get_data("111")
    get_data("222")
    
   
    failed_node = "node3"
    if failed_node in nodes:
        logging.warning(f"Manually failing node: {failed_node}")
        nodes.pop(failed_node) 

   
    get_data("111")
    get_data("222")
    
 
    nodes[failed_node] = Client(("localhost", 11213))
    logging.info(f"Manually restored node: {failed_node}")

   
    get_data("111")
    get_data("222")


if __name__ == "__main__":
    manual_failover_test()

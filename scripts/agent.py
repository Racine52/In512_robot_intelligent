__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *
from random import randint

from threading import Thread
import numpy as np
from time import sleep


class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):
        #TODO: DEINE YOUR ATTRIBUTES HERE
        
        self.key_position = None
        self.box_position = None

        #DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]   #initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]   #environment dimensions
        cell_val = env_conf["cell_val"] #value of the cell the agent is located in
        print(cell_val)
        Thread(target=self.msg_cb, daemon=True).start()
        print("hello")
        self.wait_for_connected_agent()

        
    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            print('HEDER : ', msg["header"])
            self.msg = msg
            if msg["header"] == MOVE:
                self.x, self.y =  msg["x"], msg["y"]
                print(self.x, self.y)
            elif msg["header"] == GET_NB_AGENTS:
                self.nb_agent_expected = msg["nb_agents"]
            elif msg["header"] == GET_NB_CONNECTED_AGENTS:
                self.nb_agent_connected = msg["nb_connected_agents"]
            elif msg["header"] == GET_ITEM_OWNER:
                self.owner = msg["owner"]
                self.process_item(msg, is_broadcast=False)
            elif msg["header"] == BROADCAST_MSG:
                self.process_item(msg, is_broadcast=True)

            print("hellooo: ", msg)
            print("agent_id ", self.agent_id)
            print("key ", self.key_position)
            print("box", self.box_position)
    

    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("both connected!")
                check_conn_agent = False
                
    def process_item(self, msg, is_broadcast=False):
        """ Process the item received from the server """
        print('Processing item...')
        
        # Récupération correcte du type d'item en fonction du contexte
        item_type = msg.get("Msg type" if is_broadcast else "type", None)
        owner = msg.get("owner", None)
        position = msg.get("position", (self.x, self.y)) if is_broadcast else (self.x, self.y)
        
        if owner == self.agent_id:
            if item_type == KEY_TYPE and self.key_position is None :
                self.key_position = position
                print("I have my key!")
            elif item_type == BOX_TYPE and self.box_position is None:
                self.box_position = position
                print("I have my box!")
        
        if not is_broadcast:
            cmds = {"header": BROADCAST_MSG, "Msg type": item_type, "position": position, "owner": owner}
            agent.network.send(cmds)

 
if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    
    try:    #Manual control test0
        while True:
            cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
            if cmds["header"] == BROADCAST_MSG:
                cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                cmds["position"] = (agent.x, agent.y)
                agent.network.send({"header": GET_ITEM_OWNER})
                cmds["owner"] = agent.owner
            elif cmds["header"] == MOVE:
                cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
            agent.network.send(cmds)
    except KeyboardInterrupt:
        pass
# it is always the same location of the agent first location




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

list_dir = [UP, DOWN, LEFT, RIGHT]
inv_ = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT, UP_LEFT: DOWN_RIGHT, UP_RIGHT: DOWN_LEFT, DOWN_LEFT: UP_RIGHT, DOWN_RIGHT: UP_LEFT}


class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):
        #TODO: DEINE YOUR ATTRIBUTES HERE
        self.mode = CLASSIQUE
        self.prev_dir = []

        self.cell_vall = np.float64(0.0)
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

        self.layout = np.zeros((self.w, self.h), dtype=int).T


        cell_val = env_conf["cell_val"] #value of the cell the agent is located in
        # print(cell_val)
        Thread(target=self.msg_cb, daemon=True).start()
        # print("hello")
        self.wait_for_connected_agent()

        
    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            print('HEADER : ', msg["header"])
            self.msg = msg
            if msg["header"] == MOVE:
                self.x, self.y =  msg["x"], msg["y"]
                self.cell_vall = msg["cell_val"]
                self.check_mode()
                # print(self.x, self.y)
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

    def debug(self, msgs):
        print("-------------------------------------")
        print("               DEBUG")
        print("       -----------------------")
        for msg in msgs:
            print(msg)
        print("-------------------------------------")
        with open(f'debug_{self.agent_id}.log', 'a') as f:
            f.write("-------------------------------------\n")
            for msg in msgs:
                f.write(msg + "\n")
            f.write("-------------------------------------\n")

    

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

        
        
        
        if item_type == KEY_TYPE and self.keys_positions[owner] is None :
            self.keys_positions[owner] = position
            # print("I have my key!")
        elif item_type == BOX_TYPE and self.boxes_positions[owner] is None:
            self.boxes_positions[owner] = position
            # print("I have my box!")
        
        
        # self.debug([f"item_type: {item_type}" ,f"owner: {owner}", f"position: {position}"
        #             , f"keys_positions: {self.keys_positions}", f"boxes_positions: {self.boxes_positions}"])
        
        if not is_broadcast:
            cmds = {"header": BROADCAST_MSG, "Msg type": item_type, "position": position, "owner": owner}
            agent.network.send(cmds)

    #TODO: CREATE YOUR METHODS HERE...

    def build_info(self):
        self.keys_positions = [None for _ in range( self.nb_agent_expected)]
        self.boxes_positions = [None for _ in range(self.nb_agent_expected)]

    def build_transformation(self):
        t = np.pi / 2
        r1 = np.array([[np.cos(t), - np.sin(t), 0, 0],
                       [np.sin(t), np.cos(t), 1, 0], 
                       [0, 1, 0, 0], 
                       [0, 0, 0, 1]])
        t = np.pi
        r2 = np.array([[1, 0, 0, 0],
                       [0, np.cos(t), -np.sin(t), 0], 
                       [0, np.sin(t), np.cos(t), 0], 
                       [0, 0, 0, 1]])
        
        self.transform =  np.dot(r1, r2)

    def layout_to_map(self, x:int, y:int) -> tuple:
        tmp = np.dot(self.transform, np.array([x, y, 0, 1]))[:2]

        return int(tmp[0]), int(tmp[1])

    def update_layout(self):
        with open(f"layout_{self.agent_id}.txt", "w") as f:
                for row in self.layout:
                    f.write(" ".join(map(str, row)) + "\n") 

    def build_layout(self):
        self.update_layout()
        if self.w >= self.h:

            nb_lines = int(np.ceil(self.w / 4) // 2 * 2)
            for i in range(int(nb_lines/2)):
                self.layout[2:self.h-2, 2 + (5 * i)] = 1
            for i in range(int(nb_lines/2)):
                self.layout[2:self.h-2, self.w - 3 - (5 * i)] = 1


            self.layout[2, 2:self.w-3] = 1

            self.update_layout()
            
        else:
            pass
    
    def attribute(self):
        zone_width = (self.w - 4) // self.nb_agent_expected
        self.zone_start = self.agent_id * zone_width + 2
        self.zone_end = self.zone_start + zone_width

    def find_path(self, end:tuple, start = None) -> list:
        if start is None:
            start = (self.x, self.y)
        path = []
        x1, y1 = start
        x2, y2 = end

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            path.append((x1, y1))
            if (x1, y1) == (x2, y2):
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

        return path[1:]

    def find_neighbour(self, target = None) -> tuple:
        if target is None:
            target = (self.x, self.y)

        n, m = self.layout.shape
        min_dist = float("inf")
        closest_point = None

        for i in range(n):
            for j in range(m):
                if self.layout[i][j] == 1:
                    dist = abs(i - target[1]) + abs(j - target[0])
                    if dist < min_dist:
                        min_dist = dist
                        closest_point = (i, j)
        # print(f"Agent position: ({self.x}, {self.y})")                
        # print(f"Closest point: {closest_point}")

        return closest_point
    
    def find_item(self):
        

        vals = {UP: 0, DOWN: 0, LEFT: 0, RIGHT: 0}

        while self.cell_vall != np.float64(1.0):
            
            for i in list_dir:
                self.move(i)
                vals[i] = self.cell_vall
                if self.cell_vall == np.float64(1.0):
                    break
                self.move(inv_[i])
            
            direction = 0
            
            if self.cell_vall == np.float64(1.0):
                self.network.send({"header": GET_ITEM_OWNER})
                # print(f"Item found at position: ({self.x}, {self.y})")
                return
            elif (vals[UP] == vals[RIGHT]) and (vals[UP] > vals[LEFT]) and (vals[UP] > vals[DOWN]):
                direction = UP_RIGHT
            elif (vals[UP] == vals[LEFT]) and (vals[UP] > vals[RIGHT]) and (vals[UP] > vals[DOWN]):
                direction = UP_LEFT
            elif (vals[DOWN] == vals[RIGHT]) and (vals[DOWN] > vals[LEFT]) and (vals[DOWN] > vals[UP]):
                direction = DOWN_RIGHT
            elif (vals[DOWN] == vals[LEFT]) and (vals[DOWN] > vals[RIGHT]) and (vals[DOWN] > vals[UP]):
                direction = DOWN_LEFT
            elif (vals[UP] == vals[DOWN]) and (vals[LEFT] > vals[RIGHT]):
                direction = LEFT
            elif (vals[UP] == vals[DOWN]) and (vals[LEFT] < vals[RIGHT]):
                direction = RIGHT
            elif (vals[RIGHT] == vals[LEFT]) and (vals[DOWN] > vals[UP]):
                direction = DOWN
            elif (vals[RIGHT] == vals[LEFT]) and (vals[DOWN] < vals[UP]):
                direction = UP
            else:
                # print('je suis dans ce cas de figure')
                # print(vals)
                direction = max(vals, key=vals.get)
            #     print(direction)
            
            # print(f"Direction: {direction} -----------------------------------------")
            # print(f"cell value: {self.cell_vall}")
            with open('direction.txt', 'a') as f:
                f.write("vals" + str(vals)+"\n")
                f.write("direction " + str(direction)+"\n")
                f.write("cell value: " + str(self.x) + ', ' + str(self.y) + "\n\n")
                

            self.move(direction)
            self.prev_dir.append(direction)
            self.network.send({"header": GET_ITEM_OWNER})
            vals = {UP: 0, DOWN: 0, LEFT: 0, RIGHT: 0}

            

        # print(f"Item found at position: ({self.x}, {self.y})")
        return


            
            





        # prev_pos = [(self.x, self.y)]
        # prev_val = [self.msg["cell_val"]]

        # mode = 0 if prev_dir == LEFT or prev_dir == RIGHT else 1

        # if mode == 0:
        #     # Handle previous direction being LEFT
        #     cmds = {"header": MOVE, "direction": UP}
        #     self.network.send(cmds)
        #     prev_val.append(self.msg["cell_val"])
        #     move = 0
            
        #     while self.msg["cell_val"] < 0.7:

        #         if prev_val[-1] > prev_val[-2]:
        #             move = UP
        #         elif prev_val[-1] < prev_val[-2]:
        #             move = DOWN
        #         elif prev_val[-1] == prev_val[-2]:
        #             mode = 1
        #             break


        #         cmds = {"header": MOVE, "direction": move}
        #         self.network.send(cmds)
        #         prev_val.append(self.msg["cell_val"])
        # else:
        #     # Handle previous direction being LEFT
        #     cmds = {"header": MOVE, "direction": RIGHT}
        #     self.network.send(cmds)
        #     prev_val.append(self.msg["cell_val"])
        #     move = 0
            
        #     while self.msg["cell_val"] < 0.7:

        #         if prev_val[-1] > prev_val[-2]:
        #             move = RIGHT
        #         elif prev_val[-1] < prev_val[-2]:
        #             move = LEFT
        #         elif prev_val[-1] == prev_val[-2]:
        #             mode = 0
        #             break


        #         cmds = {"header": MOVE, "direction": move}
        #         self.network.send(cmds)
        #         prev_val.append(self.msg["cell_val"])

    def check_mode(self):
        if self.mode == GOTARGET: 
            return
        
        def is_near(x, y, positions):
            """Vérifie si (x, y) est proche de l'une des positions (±2)."""
            return any(
                pos is not None and abs(x - pos[0]) <= 2 and abs(y - pos[1]) <= 2 
                for pos in positions
            )

        cell_val_condition = self.msg["cell_val"] in [0.3, 0.6, 0.25, 0.5]
        near_keys = is_near(self.x, self.y, self.keys_positions)
        near_boxes = is_near(self.x, self.y, self.boxes_positions)
                  
        if cell_val_condition and not (near_keys or near_boxes):
            
            if self.mode == CLASSIQUE:
                self.mode = RESSEARCHANDDESTROY
        else:
            if self.mode == RESSEARCHANDDESTROY:
                self.mode = CLASSIQUE

    def move(self, direction:int):
        
        cmds = {"header": MOVE, "direction": direction}
        
        self.network.send(cmds)
        sleep(0.5)

    def back_on_track(self):
        for i in self.prev_dir:
            self.move(inv_[i])
        self.prev_dir = []
    
    def follow_path(self, path):

        x1, y1 = self.x, self.y

        direction = None
        
        for i in path:
            
            x2, y2 = i
            if x2 > x1 and y2 == y1:
                direction = RIGHT
            elif x2 < x1 and y2 == y1:
                direction = LEFT
            elif x2 == x1 and y2 > y1:
                direction = DOWN
            elif x2 == x1 and y2 < y1:
                direction = UP
            elif x2 > x1 and y2 > y1:
                direction = DOWN_RIGHT
            elif x2 > x1 and y2 < y1:
                direction = UP_RIGHT
            elif x2 < x1 and y2 > y1:
                direction = DOWN_LEFT
            elif x2 < x1 and y2 < y1:
                direction = UP_LEFT

            self.move(direction)
            x1, y1 = self.x, self.y

            if self.mode == RESSEARCHANDDESTROY:
                self.find_item()
                self.back_on_track()

            elif not self.mode == GOTARGET:
                if all(pos is not None for pos in self.keys_positions) and all(pos is not None for pos in self.boxes_positions):
                    self.mode = GOTARGET
                    # self.debug([f'MODE {self.mode}'])
                    return True
            
              

    def A_star(self, end) -> list:
        start = (self.x, self.y)
        open_set = set()
        open_set.add(start)
        came_from = {}

        g_score = {start: 0}
        f_score = {start: abs(start[0] - end[0]) + abs(start[1] - end[1])}

        while open_set:
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            open_set.remove(current)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.w and 0 <= neighbor[1] < self.h and self.layout[neighbor[1]][neighbor[0]] == 1:
                    tentative_g_score = g_score[current] + 1
                    if tentative_g_score < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + abs(neighbor[0] - end[0]) + abs(neighbor[1] - end[1])
                        open_set.add(neighbor)

        return []

    def find_fork(self) -> list:
        layout_path = []

        r = self.zone_end + 1 if self.agent_id == (self.nb_agent_expected - 1) else self.zone_end
        for i in range(self.zone_start, r ):
            if self.layout[self.h - 3, i] == 1:
                layout_path.append((i, self.h - 3))
        
        return layout_path

    def get_target(self):
        
        key_pos = self.keys_positions[self.agent_id]

        key_neighbour = self.find_neighbour(key_pos)
        key_neighbour = self.layout_to_map(key_neighbour[0], key_neighbour[1])
    
        key_path = self.A_star(key_neighbour) + self.find_path(key_pos, key_neighbour)
        

        self.follow_path(key_path)

        box_pos = self.boxes_positions[self.agent_id]

        box_neighbour = self.find_neighbour(box_pos)
        box_neighbour = self.layout_to_map(box_neighbour[0], box_neighbour[1])

        agent_neighbour = self.find_neighbour()
        agent_neighbour = self.layout_to_map(agent_neighbour[0], agent_neighbour[1])
        
        self.follow_path(self.find_path(agent_neighbour))
        self.follow_path(self.A_star(box_neighbour) + self.find_path(box_pos, box_neighbour))


    




        
        


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
                agent.network.send(cmds)
            elif cmds["header"] == MOVE:
                cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
                agent.network.send(cmds)
            elif cmds["header"] == MAPPING:
                agent.build_transformation()
                agent.build_layout()
                agent.attribute()
                agent.build_info()

                
                x, y = agent.find_neighbour()
                # print(f"Neighbour: ({x}, {y})")
                # print("transform: ", agent.layout_to_map(x, y))
                end = agent.layout_to_map(x, y)
                path = agent.find_path(end)
                # print(f"Path 1: {path}")
                agent.follow_path(path)
                
                # print(f"Position: ({agent.x}, {agent.y})")
                path = agent.A_star((agent.zone_start,2))
                # print(f"Path 2: {path}")
                agent.follow_path(path)
                # print(agent.nb_agent_expected)
                # print(f"Agent {agent.agent_id} is responsible for the zone {agent.zone_start} - {agent.zone_end}")

                fork = agent.find_fork()
                # print(f"Fork: {fork}")

                for i in fork:
                    path = agent.A_star(i)
                    if agent.follow_path(path):
                        break
            
                agent.get_target()
                
                
            
            else:
                agent.network.send(cmds)
    except KeyboardInterrupt:
        pass
# it is always the same location of the agent first location




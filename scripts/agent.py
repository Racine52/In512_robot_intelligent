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

from menu import show_menu
list_dir = [UP, DOWN, LEFT, RIGHT]
inv_ = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT, UP_LEFT: DOWN_RIGHT, UP_RIGHT: DOWN_LEFT, DOWN_LEFT: UP_RIGHT, DOWN_RIGHT: UP_LEFT}


class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):
        #TODO: DEINE YOUR ATTRIBUTES HERE
        self.mode = GOONTRACK
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
        Thread(target=self.msg_cb, daemon=True).start()
        self.wait_for_connected_agent()
        sleep(3)
        self.build_info()
        self.debug(['keys_positions', str(self.keys_positions), 'boxes_positions', str(self.boxes_positions)])



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
        """
        Prints debug messages to the console and to a log file.

        Parameters:
        - msgs (list of str): A list of debug messages to be printed.

        Returns:
        - None

        The debug messages are printed with a header and footer for clarity.
        Each message is printed on a new line.
        The debug messages are also written to a log file named 'debug_{self.agent_id}.log'.
        """
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
        """
        This function sends a request to the server to get the number of connected agents.
        It then waits until the number of expected agents (self.nb_agent_expected) is equal to the number of connected agents.

        Parameters:
        None

        Returns:
        None
        """
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("both connected!")
                check_conn_agent = False
                
    def process_item(self, msg, is_broadcast=False):
        """
        Process the item received from the server.

        Parameters:
        msg (dict): The message received from the server. It should contain the following keys:
            - "Msg type" or "type" (int): The type of the item.
            - "owner" (int): The owner of the item.
            - "position" (tuple): The position of the item.

        is_broadcast (bool): A flag indicating whether the message is a broadcast message.

        Returns:
        None
        """
        print('Processing item...')

        # Retrieve the correct item type based on the context
        item_type = msg.get("Msg type" if is_broadcast else "type", None)
        owner = msg.get("owner", None)
        position = msg.get("position", (self.x, self.y)) if is_broadcast else (self.x, self.y)


        if item_type == KEY_TYPE and self.keys_positions[owner] is None :
            self.keys_positions[owner] = position
            # print("I have my key!")
        elif item_type == BOX_TYPE and self.boxes_positions[owner] is None:
            self.boxes_positions[owner] = position
            # print("I have my box!")


        self.debug([f"item_type: {item_type}" ,f"owner: {owner}", f"position: {position}"
                    , f"keys_positions: {self.keys_positions}", f"boxes_positions: {self.boxes_positions}"])

        if not is_broadcast:
            cmds = {"header": BROADCAST_MSG, "Msg type": item_type, "position": position, "owner": owner}
            agent.network.send(cmds)

    #TODO: CREATE YOUR METHODS HERE...

    def build_info(self):
        """
        This function initializes the positions of keys and boxes for all agents.
        It initializes the keys_positions and boxes_positions lists with None values, 
        representing the unknown positions of keys and boxes for each agent.

        Parameters:
        None

        Returns:
        None
        """
        self.keys_positions = [None for _ in range( self.nb_agent_expected)]
        self.boxes_positions = [None for _ in range(self.nb_agent_expected)]

    def build_transformation(self):
        """
        This function builds a transformation matrix for mapping the agent's position in the layout.

        The transformation matrix is a 4x4 numpy array that represents a rotation and translation.
        The rotation is performed first by pi/2 radians (90 degrees) around the y-axis, 
        followed by a rotation of pi radians (180 degrees) around the x-axis.

        Parameters:
        None

        Returns:
        None
        """
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

    def layout_to_map(self, x: int, y: int) -> tuple:
        """
        Converts a point from the layout coordinate system to the map coordinate system.

        Parameters:
        x (int): The x-coordinate in the layout coordinate system.
        y (int): The y-coordinate in the layout coordinate system.

        Returns:
        tuple: A tuple containing the converted x and y coordinates in the map coordinate system.
        """
        tmp = np.dot(self.transform, np.array([x, y, 0, 1]))[:2]

        return int(tmp[0]), int(tmp[1])

    def map_to_layout(self, x:int, y:int) -> tuple:
        """
        Converts the given coordinates from the map to the layout.

        Parameters:
        x (int): The x-coordinate on the map.
        y (int): The y-coordinate on the map.

        Returns:
        tuple: A tuple containing the corresponding x and y coordinates on the layout.
        """
        tmp = np.dot(np.linalg.inv(self.transform), np.array([x, y, 0, 1]))[:2]

        return int(tmp[0]), int(tmp[1])

    def print_layout(self):
        """
        Prints the current state of the agent's layout to a text file.

        Parameters:
        None

        Returns:
        None

        The layout is printed row by row, with each cell separated by a space.
        The layout is saved in a file named "layout_{self.agent_id}.txt".
        """
        with open(f"layout_{self.agent_id}.txt", "w") as f:
                for row in self.layout:
                    f.write(" ".join(map(str, row)) + "\n")

    def build_layout(self):
        """
        This function builds the layout of the environment for the agents.
        The layout is a 2D numpy array representing the grid of the environment.
        The function initializes the layout with walls and paths.

        Parameters:
        None

        Returns:
        None
        """
        self.print_layout()

        nb_lines = int(np.ceil(self.w / 4) // 2 * 2)
        for i in range(int(nb_lines/2)):
            self.layout[2:self.h-2, 2 + (5 * i)] = 1
        for i in range(int(nb_lines/2)):
            self.layout[2:self.h-2, self.w - 3 - (5 * i)] = 1

        self.layout[2, 2:self.w-3] = 1

        self.print_layout()
    
    def attribute(self):
        """
        This function calculates the start and end positions of the zone each agent is responsible for.
        The zones are evenly distributed across the width of the layout, excluding the borders.

        Parameters:
        None

        Returns:
        None

        The function sets the following attributes:
        - self.zone_start: The x-coordinate of the start of the agent's zone.
        - self.zone_end: The x-coordinate of the end of the agent's zone.
        """
        zone_width = (self.w - 4) // self.nb_agent_expected
        self.zone_start = self.agent_id * zone_width + 2
        self.zone_end = self.zone_start + zone_width

    def find_path(self, end: tuple, start: tuple = None) -> list:
        """
        This function calculates the shortest path from a start point to an end point in a 2D grid.
        It uses the Bresenham's line algorithm to find the path.

        Parameters:
        - end (tuple): The (x, y) coordinates of the end point.
        - start (tuple): The (x, y) coordinates of the start point. If not provided, the current agent's position is used.

        Returns:
        - path (list): A list of (x, y) coordinates representing the shortest path from the start to the end point.
        """
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
        """
        This function finds the closest neighbour to a given target point in the layout.

        Parameters:
        - target (tuple): The (x, y) coordinates of the target point. If not provided, the current agent's position is used.

        Returns:
        - closest_point (tuple): The (x, y) coordinates of the closest neighbour to the target point.
        """
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
        """
        This function is responsible for navigating the agent to find an item in the grid.
        The agent uses a simple strategy to determine the direction to move in each step.

        Parameters:
        None

        Returns:
        None
        """
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
                #self.network.send({"header": GET_ITEM_OWNER})
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
            if self.cell_vall == np.float64(1.0): self.network.send({"header": GET_ITEM_OWNER})

            vals = {UP: 0, DOWN: 0, LEFT: 0, RIGHT: 0}
        return

    def update_layout(self, x: int, y: int, value: int) -> None:
        """
        Updates the value at the specified location (x, y) in the layout grid.

        Parameters:
        x (int): The x-coordinate of the location in the grid.
        y (int): The y-coordinate of the location in the grid.
        value (int): The new value to be assigned at the specified location.

        Returns:
        None
        """
        self.layout[y][x] = value
        
        
    def dodge_wall(self):
        """
        This function is responsible for the agent's ability to dodge walls.
        The agent navigates through the layout, updating the layout and its position as it goes.
        It uses the A* algorithm to find the optimal path to dodge the wall.
        
        Parameters:
        self (Agent): The instance of the Agent class.

        Returns:
        None
        """
        pos_init = (self.x, self.y)
        path = [pos_init]

        self.update_layout(self.x, self.y+1, 0)

        def up_right(path):
            self.move(UP)
            self.update_layout(self.x, self.y, 1)
            path.append((self.x, self.y))

            self.move(RIGHT)
            self.update_layout(self.x, self.y, 1)
            path.append((self.x, self.y))

            return path

        path = up_right(path)

        while pos_init[0] != self.x:
            if self.cell_vall == 0.35:
                self.update_layout(self.x, self.y, 0)
                path = up_right(path)

            else :
                self.move(DOWN)
                self.update_layout(self.x, self.y, 1)
                path.append((self.x, self.y))

                next_pos = (self.x-1, self.y)

                if next_pos not in path:
                    self.move(LEFT)
                    self.update_layout(self.x, self.y, 1)    
                    if self.cell_vall == 0.35:
                        self.update_layout(self.x, self.y, 0)
                        self.move(RIGHT) 
                    else :
                        while pos_init[0] != self.x:  
                            self.move(LEFT)
                            self.update_layout(self.x, self.y, 1) 

        self.print_layout()
        if all(pos is not None for pos in self.keys_positions) and all(pos is not None for pos in self.boxes_positions):
                    self.mode = GOTARGET

    def check_mode(self):
        """
        This function checks the current mode of the agent and updates it based on certain conditions.

        Parameters:
        self (Agent): The instance of the Agent class.

        Returns:
        None. The function updates the mode attribute of the Agent instance.
        """
        if self.mode == GOTARGET or self.mode == GOONTRACK: 
            if  self.cell_vall == 0.35 :
                if self.mode != DODGEWALL:
                    self.mode = DODGEWALL
            return

        def is_near(x, y, positions):
            """
            Checks if the given coordinates (x, y) are near any of the given positions (within a distance of 2).

            Parameters:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            positions (list): A list of tuples representing the positions.

            Returns:
            bool: True if (x, y) is near any of the positions, False otherwise.
            """
            return any(
                pos is not None and abs(x - pos[0]) <= 2 and abs(y - pos[1]) <= 2 
                for pos in positions
            )

        cell_val_condition = self.cell_vall in [0.3, 0.6, 0.25, 0.5]
        near_keys = is_near(self.x, self.y, self.keys_positions)
        near_boxes = is_near(self.x, self.y, self.boxes_positions)

        if  self.cell_vall == 0.35 :
            self.update_layout(self.x, self.y, 0)
            if self.mode != DODGEWALL:
                self.mode = DODGEWALL         
        elif cell_val_condition and not (near_keys or near_boxes):

            if self.mode != RESSEARCHANDDESTROY:
                self.mode = RESSEARCHANDDESTROY

        else:
            if self.mode != CLASSIQUE:
                self.mode = CLASSIQUE

        # if not self.mode == GOTARGET:
        #         if all(pos is not None for pos in self.keys_positions) and all(pos is not None for pos in self.boxes_positions):
        #             self.mode = GOTARGET
        #             self.debug([f'MODE {self.mode}'])

    def move(self, direction: int) -> None:
        """
        This function sends a move command to the server with the specified direction.

        Parameters:
        direction (int): The direction in which the agent should move. It can take values from 0 to 8, inclusive.

        Returns:
        None
        """
        cmds = {"header": MOVE, "direction": direction}

        self.network.send(cmds)
        sleep(0.5)

    def back_on_track(self):
        """
        This function is responsible for moving the agent back to its original path.
        It iterates through the list of previous directions (self.prev_dir) and sends a move command in the opposite direction for each step.
        After moving back to the original path, it clears the list of previous directions.

        Parameters:
        self (Agent): The instance of the Agent class.

        Returns:
        None
        """
        for i in self.prev_dir:
            self.move(inv_[i])
        self.prev_dir = []

    def follow_path(self, path):
        """
        This function is responsible for the agent following a given path.
        It iterates through the path, calculates the direction to move in, and sends a move command to the server.
        It also handles specific modes such as RESSEARCHANDDESTROY and DODGEWALL.

        Parameters:
        path (list): A list of tuples representing the coordinates in the layout grid.

        Returns:
        bool: True if the agent has reached the target (GOTARGET mode), False otherwise.
        """
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

            elif self.mode == DODGEWALL:
                self.dodge_wall()
                return False

            elif not self.mode == GOTARGET:
                if all(pos is not None for pos in self.keys_positions) and all(pos is not None for pos in self.boxes_positions):
                    self.mode = GOTARGET
                    self.debug([f'MODE {self.mode}'])
                    return True


    def A_star(self, end) -> list:
        """
        A* pathfinding algorithm to find the shortest path from the agent's current position to the given end position.

        Parameters:
        end (tuple): A tuple representing the end position in the layout grid.

        Returns:
        list: A list of tuples representing the path from the agent's current position to the end position.
        """
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
        """
        This function finds the fork in the layout grid, which is the point where the agents split their paths.

        Parameters:
        self (Agent): The instance of the Agent class.

        Returns:
        list: A list of tuples representing the coordinates of the fork in the layout grid.
        """
        layout_path = []

        r = self.zone_end + 1 if self.agent_id == (self.nb_agent_expected - 1) else self.zone_end
        for i in range(self.zone_start, r ):
            if self.layout[self.h - 3, i] == 1:
                layout_path.append((i, self.h - 3))
                layout_path.append((i, 2))

        return layout_path

    def get_target(self):
        """
        This function is responsible for the agent's movement to collect keys and boxes.
        It calculates the path to the nearest key and box, and then follows the path to collect them.

        Parameters:
        self (Agent): The instance of the Agent class.

        Returns:
        None. The function updates the agent's position and mode.
        """
        key_pos = self.keys_positions[self.agent_id]

        key_neighbour = self.find_neighbour(key_pos)
        key_neighbour = self.layout_to_map(key_neighbour[0], key_neighbour[1])

        key_path = self.A_star(key_neighbour) + self.find_path(key_pos, key_neighbour)

        if not self.follow_path(key_path):
            self.follow_path(self.A_star(key_neighbour) + self.find_path(key_pos, key_neighbour))


        box_pos = self.boxes_positions[self.agent_id]

        box_neighbour = self.find_neighbour(box_pos)
        box_neighbour = self.layout_to_map(box_neighbour[0], box_neighbour[1])

        box_path = self.A_star(box_neighbour) + self.find_path(box_pos, box_neighbour)

        agent_neighbour = self.find_neighbour()
        agent_neighbour = self.layout_to_map(agent_neighbour[0], agent_neighbour[1])

        self.follow_path(self.find_path(agent_neighbour))
        if not self.follow_path(box_path):
            self.follow_path(self.A_star(box_neighbour) + self.find_path(box_pos, box_neighbour))

    def wait(self):
        """
        This function is responsible for the agent's waiting behavior.
        The agent continuously follows its current position until it reaches the GOTARGET mode.

        Parameters:
        self (Agent): The instance of the Agent class.

        Returns:
        None. The function continuously follows the agent's position until it reaches the GOTARGET mode.
        """
        while True:
            self.follow_path([(self.x, self.y)])
            if self.mode == GOTARGET:
                break

if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)



    try:    #Manual control test0
        while True:
            # cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}

            sleep(0.5)
            cmds = {"header": show_menu()}
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

                agent.mode = CLASSIQUE
                fork = agent.find_fork()
                # print(f"Fork: {fork}")

                for i in fork:
                    path = agent.A_star(i)
                    if agent.follow_path(path):
                        break
                    else :
                        path = agent.A_star(i)
                        agent.follow_path(path)

                agent.debug(['Wait'])
                agent.wait()
                agent.debug(['Stop Wait'])

                agent.get_target()



            else:
                agent.network.send(cmds)
    except KeyboardInterrupt:
        pass
# it is always the same location of the agent first location

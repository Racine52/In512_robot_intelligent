# Distributed Intelligence for Robots

This project implements a distributed intelligence system for robots tasked with solving a sequence of challenges:

1. Find their assigned key.
2. Use the key to unlock their assigned box.

Each robot operates independently, using the same algorithm, but without sharing memory. The system is configurable, allowing adjustments to the number of robots, the map layout, and the number of obstacles.

---

## Features

- **Multiple Robots**: Operate simultaneously and independently.
- **Configurable Maps**: Choose from different layouts and levels of complexity.
- **Customizable Parameters**: Easily adjust the number of robots, map design, and obstacles.

---

## Installation

To download and set up the project, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/Racine52/In512_robot_intelligent.git
   ```
2. Navigate to the project directory:

   ```bash
   cd In512_robot_intelligentcd your-repo-name
   ```
3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

1. Run `./scriptserver.py`, which accepts the following parameters:

- `-nb`: Number of robots (1-4).
- `-mi`: Map ID (1-3).
- `-nw`: Number of walls/obstacles (0-3).

```bash
python ./scripts/server.py -nb 3 -mi 2 -nw 1 #On windows
python ./scripts/server.py -nb 3 -mi 2 -nw 1 #On Mac OS
```

In this example for server:

- **3 robots** will be active.
- The program will use **Map 2**.
- The map will include **1 additional obstacle**.


2. Open nb other terminals and run, **for each of them**

```bash

python scripts/agent.py #On windows
python3 scripts/agent.py #On Mac OS
```

Once each terminals run the agent script, the environment should appear on the computer that hosts the server.

---

## Contributors

This project was created and maintained by:

- Tristan MAILLE
- Titouan MILLET
- Louan VANTHORRE

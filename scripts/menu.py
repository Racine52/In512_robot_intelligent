from rich.console import Console
from rich.panel import Panel
from rich.text import Text
 
def show_menu():
    console = Console()

    menu_text = Text()


    menu_text.append("██╗███╗   ██╗    ███████╗ ██╗██████╗  \n", style="bold blue")
    menu_text.append("██║████╗  ██║    ██╔════╝███║╚════██╗ \n", style="bold blue")
    menu_text.append("██║██╔██╗ ██║    ███████╗╚██║ █████╔╝ \n", style="bold blue")
    menu_text.append("██║██║╚██╗██║    ╚════██║ ██║██╔═══╝  \n", style="bold blue")
    menu_text.append("██║██║ ╚████║    ███████║ ██║███████╗ \n", style="bold blue")
    menu_text.append("╚═╝╚═╝  ╚═══╝    ╚══════╝ ╚═╝╚══════╝ \n", style="bold blue")
                                     
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
    menu_text.append("0 -> Broadcast message\n", style="bold magenta")
    menu_text.append("1 -> Get data\n", style="bold magenta")
    menu_text.append("2 -> Move\n", style="bold magenta")
    menu_text.append("3 -> Get number of connected agents\n", style="bold magenta")
    menu_text.append("4 -> Get number of agents\n", style="bold magenta")
    menu_text.append("5 -> Get item owner\n", style="bold magenta")
    menu_text.append("6 -> Start autonomous mode", style="bold magenta")

    panel = Panel(menu_text, title="Main Menu", title_align="center", border_style="red", expand=False)

    console.print(panel)
    choice = console.input("[bold yellow]Enter your choice [0-6]: [/]")
    return int(choice)


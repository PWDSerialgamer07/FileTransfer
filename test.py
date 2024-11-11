from textual.app import App, ComposeResult
from textual.widgets import Static


class Ips_returned(Static):
    def compose(self) -> ComposeResult:
        yield Static("Ips returned:", classes="box", id="ips_returned")


class Console(Static):
    def compose(self) -> ComposeResult:
        yield Static("Console:", classes="box", id="console")


class User_ip_input(Static):
    def compose(self) -> ComposeResult:
        yield Static("Enter your choice:", classes="box", id="user_ip_input")


class Discovery(App):
    CSS_PATH = "Tcss/grid_layout.tcss"

    def compose(self) -> ComposeResult:
        yield Ips_returned()
        yield Console()
        yield User_ip_input()


# Save this script as discovery_app.py and ensure your CSS file is correctly placed in the Tcss folder.
if __name__ == "__main__":
    app = Discovery()
    app.run()

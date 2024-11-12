from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Label
from textual.containers import Center, VerticalScroll
ip = None


class Discovery(App):
    CSS_PATH = "Tcss/grid_layout.tcss"

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="ips_returned")
        yield VerticalScroll(id="console")
        yield Input(placeholder="Enter your choice", id="user_ip_input", type="integer")

    def on_input_submitted(self) -> None:
        self.choose_ip()

    def choose_ip(self) -> None:
        text_value = self.query_one(Input).value
        try:
            value = int(text_value)
        except ValueError:
            self.query_one("#console").mount(Label("Invalid input"))
            self.query_one("#user_ip_input").value = ""
            return
        self.query_one("#console").mount(Label(f"{value} has been chosen"))
        self.query_one("#user_ip_input").value = ""


        # Save this script as discovery_app.py and ensure your CSS file is correctly placed in the Tcss folder.
if __name__ == "__main__":
    app = Discovery()
    app.run()

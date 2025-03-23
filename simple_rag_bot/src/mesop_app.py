import mesop as me

ROOT_BOX_STYLE = me.Style(
    background="#e7f2ff",
    height="100%",
    font_family="Inter",
    display="flex",
    flex_direction="column",
)

@me.page(
    path="/",
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap"
    ],
)
def app():
    with me.box(style=me.Style(
        display="grid",
        grid_template_columns="250px 1fr 250px",
        height="100%"
    )):
        # Sidebar
        with me.box(style=me.Style(
            background="#ffffff",
            padding=me.Padding.all(24),
            overflow_y="auto"
        )):
            me.text("Sidebar")
            items=["Conversation 1", "Conversation 2", "Conversation 3"]
            for item in items:
                me.button(item)
            with me.content_button(type="icon"):
                me.icon(icon="help")

        # Main content
        with me.box(style=me.Style(
            background="#e7f2ff",
            padding=me.Padding.all(24),
            overflow_y="auto",
            flex_direction="column",
            flex_grow=1,
        )):
            page()

        # Settings
        with me.box(style=me.Style(
            background="#f0f0f0",
            padding=me.Padding.all(24),
            overflow_y="auto"
        )):
            me.text("Settings")

def page():
    with me.box(style=ROOT_BOX_STYLE):
        header()
        with me.box(
            style=me.Style(
                width="min(680px, 100%)",
                margin=me.Margin.symmetric(
                    horizontal="auto",
                    vertical=36,
                ),
                display='flex',
                flex_direction='column',
                height='100%'
            )
        ):
            with me.box(style=me.Style(flex_grow=1, display='flex', flex_direction='column-reverse', overflow_y='auto')):
                me.text(
                    "Good Morning, Ruths",
                    style=me.Style(
                        font_size=20,
                        margin=me.Margin(bottom=24),
                        justify_content="center"
                    ),
                )
                # Add chat messages here later.
                # Example: me.text("Message 1")
                # Example: me.text("Message 2")

            chat_input()

def header():
    with me.box(
        style=me.Style(
            padding=me.Padding.all(16),
        ),
    ):
        me.text(
            "Simple RAG Bot",
            style=me.Style(
                font_weight=500,
                font_size=24,
                color="#3D3929",
                letter_spacing="0.3px",
            ),
        )

@me.stateclass
class State:
    input: str = ""

def on_blur(e: me.InputBlurEvent):
    state = me.state(State)
    state.input = e.value

def chat_input():
    state = me.state(State)
    with me.box(
        style=me.Style(
            border_radius=16,
            padding=me.Padding.all(8),
            background="white",
            display="flex",
            width="100%"
        )
    ):
        with me.box(style=me.Style(flex_grow=1)):
            me.native_textarea(
                value=state.input,
                placeholder="Enter a prompt",
                on_blur=on_blur,
                style=me.Style(
                    padding=me.Padding(top=10, left=16),
                    outline="none",
                    width="100%",
                    border=me.Border.all(me.BorderSide(style="none")),
                ),
            )
        with me.content_button(type="icon", on_click=send_prompt):
            me.icon("send")

def send_prompt(e: me.ClickEvent):
    state = me.state(State)
    print(f"Sending prompt: {state.input}")
    state.input = ""
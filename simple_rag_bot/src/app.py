import mesop as me
# import mesop.labs as mel
from mesop_chat import chat, ChatMessage

CHAT_CONTAINER_STYLE = me.Style(
    background=me.theme_var("surface"),
    height="100%",
    font_family="Inter",
    display="flex",
    flex_direction="column",
)

@me.page(path="/",
         title="Simple RAG App",
         stylesheets=[
             "https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap"
         ])
def app_screen():
    with me.box(style=me.Style(
        display="grid",
        grid_template_columns="250px 1fr 250px",
        height="100%"
    )):
        # Left Sidebar
        with me.box(style=me.Style(
            background=me.theme_var("surface-container-low"),
            overflow_y="auto"
        )):
            with me.content_button(type="raised", style=me.Style(
                width=200,
                display="flex",
                flex_direction="row",
                align_items="center",
                justify_content= "space-between",
                border_radius="10px",
                margin=me.Margin.symmetric(vertical=20, horizontal="auto")
            )):
                with me.box(style=me.Style(
                    display="flex",
                    flex_direction="row",
                    align_items="center",
                    justify_content= "space-between"
                )):
                    me.icon(icon="add")
                    me.text(text="New Conversation")
        
        # Chat Container
        with me.box(style=me.Style(
            background=me.theme_var("surface"),
            overflow_y="auto",
            flex_direction="column",
            flex_grow=1,
        )):
            chat_container()
        
        # Settings bar
        with me.box(style=me.Style(
            background=me.theme_var("surface-container-low"),
            overflow_y="auto",
        )):
            me.text(text="Settings",
                    style=me.Style(
                    font_size=16,
                    color="#3D3929",
                    letter_spacing="0.3px",
                    padding=me.Padding.all(20)
                ))
            model_options = [
                me.SelectOption(label="Gemini 1.5 Pro", value="gemini-1.5-pro"),
                me.SelectOption(label="Gemini 1.5 Flash", value="gemini-1.5-flash"),
                me.SelectOption(label="Gemini 2.0 Flash", value="gemini-2.0-flash"),
            ]
            me.select(options=model_options,
                      label="Model",
                      style=me.Style(
                          width=210,
                          height=80,
                          font_size=14,
                          border_radius=20,
                          color="#ffffff"))
            me.slider(value=1024,
                      min=200,
                      max=8096,
                      discrete=True,
                      style=me.Style(
                          width=200,
                          height=50,
                          font_size=14
                          ))


def chat_container():
    with me.box(style=CHAT_CONTAINER_STYLE):
        # chat_header()
        # mel.chat(transform, title="Simple RAG App", bot_user="Assistant")
        chat(transform, title="Good Morning, Ruths", bot_user="Assistant")
        # with me.box(style=me.Style(
        #     display="flex",
        #     flex_direction="row"
        # )):
        #     me.icon(icon="face")
        #     me.text("This is a big chunk of text. <br> dsvbauyshsvbfahvljhvfbKJAH")

def chat_header():
    with me.box(style=me.Style(
        padding=me.Padding.all(16),
        display="flex",
        align_items="center",
        justify_content="center",
    )):
        me.text(text="Good Morning, Ruths",
                style=me.Style(
                    font_size=36,
                    color="#3D3929",
                    letter_spacing="0.3px",
                ))

def transform(input: str, history: list[ChatMessage]):
  return f"Echo: {input}"
    
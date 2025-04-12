from enum import Enum
import mesop as me
# import mesop.labs as mel
from mesop_chat import chat, ChatMessage
from backend.core.chat import generate_response, generate_rag_response

class ModelOptions(Enum):
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"

model_mapping = {
    ModelOptions.GEMINI_2_0_FLASH: "Gemini 2.0 Flash",
    ModelOptions.GEMINI_1_5_PRO: "Gemini 1.5 Pro",
    ModelOptions.GEMINI_1_5_FLASH: "Gemini 1.5 Flash",
}

CHAT_CONTAINER_STYLE = me.Style(
   background=me.theme_var("surface"),
   height="100%",
   font_family="Inter",
   display="flex",
   flex_direction="column",
)

MODEL_SELECT_STYLE = me.Style(
   width="95%",
   height=80,
   font_size=14,
   border_radius=20,
   margin=me.Margin(top=40),
   color=me.theme_var("surface")
)

model_options = [
    me.SelectOption(label=label, value=option.value)
    for option, label in model_mapping.items()
]

@me.stateclass
class State:
  default_model: str = model_options[0].value
  initial_max_tokens_value: str = "1024"
  initial_tokens_slider_value: int = 1024
  tokens_slider_value: int = 1024

def on_selection_change_2(e: me.SelectSelectionChangeEvent):
  s = me.state(State)
  s.default_model = e.value

def on_value_change(event: me.SliderValueChangeEvent):
  state = me.state(State)
  state.tokens_slider_value = int(event.value)
  state.initial_max_tokens_value = str(state.tokens_slider_value)

def on_input(event: me.InputEvent):
  state = me.state(State)
  # When made empty, throws an error
  if event.value == "":
     event.value = 0
  state.initial_tokens_slider_value = int(event.value)
  state.tokens_slider_value = state.initial_tokens_slider_value

@me.page(path="/",
         title="Simple RAG App",
         stylesheets=[
             "https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap"
         ])
def app_screen():
    with me.box(style=me.Style(
        display="grid",
        grid_template_columns="250px 1fr",
        height="100%"
    )):
        # Left Sidebar
        left_sidebar()

        # Chat Container
        with me.box(style=me.Style(
            background=me.theme_var("surface"),
            overflow_y="auto",
            flex_direction="column",
            flex_grow=1,
        )):
            chat_container()
        
        # Settings bar
        # settings_sidebar()

def left_sidebar():
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
            margin=me.Margin.symmetric(vertical=20, horizontal="auto"),
            background=me.theme_var("secondary-container")
        )):
            with me.box(style=me.Style(
                display="flex",
                flex_direction="row",
                align_items="center",
                justify_content= "space-between"
            )):
                me.icon(icon="add")
                me.text(text="New Conversation")

def chat_container():
    with me.box(style=CHAT_CONTAINER_STYLE):
        chat(generate_rag_response, title="Good Morning, Ruths", bot_user="Assistant")

def settings_sidebar():
   state = me.state(State)
   with me.box(style=me.Style(background=me.theme_var("surface-container-low"), overflow_y="auto",overflow_x="hidden")):
    me.text(text="Settings",
            style=me.Style(
               font_size=18,
               letter_spacing="0.3px",
               padding=me.Padding.all(20)
            ))
    
    me.select(options=model_options,
                label="Model",
                multiple=False,
                appearance="outline",
                value=state.default_model,
                style=MODEL_SELECT_STYLE)
    
    with me.box(style=me.Style(display="flex", flex_direction="column", margin=me.Margin.all(5))):
        me.input(
            label="Max tokens",
            appearance="outline",
            value=str(int(state.initial_max_tokens_value)),
            on_input=on_input,
            )
        me.slider(on_value_change=on_value_change,
                  value=state.initial_tokens_slider_value,
                  min=0,
                  max=8192,
                  step=256,
                  discrete=True,
                  style=me.Style(
                    width="90%",
                    height=50,
                    font_size=14,
                    margin=me.Margin(left=5, right=5)
                ))
        with me.box(
            style=me.Style(
            display="flex", flex_direction="row",justify_content= "space-between",margin=me.Margin(right=10)
        )):
            me.text("0")
            me.text("8192")

# def transform(input: str, history: list[ChatMessage]):
  
    
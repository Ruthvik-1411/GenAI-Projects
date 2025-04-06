import time
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any, Callable, Generator, Literal

import mesop as me

Role = Literal["user", "assistant"]
ACCEPTED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf","video/mp4"]

_ROLE_USER = "user"
_ROLE_ASSISTANT = "assistant"

_BOT_USER_DEFAULT = "assistant"

_COLOR_BACKGROUND = me.theme_var("background")
_COLOR_CHAT_BUBBLE_YOU = me.theme_var("surface")
# https://m3.material.io/styles/color/roles
_COLOR_CHAT_BUBBLE_BOT = me.theme_var("surface-container-low")

_DEFAULT_PADDING = me.Padding.all(5)
_DEFAULT_BORDER_SIDE = me.BorderSide(
  width="1px", style="solid", color=me.theme_var("secondary-fixed")
)

_LABEL_BUTTON = "attach_file"
_LABEL_BUTTON_IN_PROGRESS = "pending"
_LABEL_INPUT = "Type your message here."

_STYLE_APP_CONTAINER = me.Style(
  background=_COLOR_BACKGROUND,
  display="flex",
  align_content="start",
  flex_direction="column",
  height="100%",
  margin=me.Margin.symmetric(vertical=0, horizontal="auto"),
  width="min(1024px, 100%)",
  box_shadow=("0 3px 1px -2px #0003, 0 2px 2px #00000024, 0 1px 5px #0000001f"),
  padding=me.Padding(top=20, left=20, right=20),
)
_STYLE_TITLE = me.Style(padding=me.Padding(left=10),display="flex",
  align_items="center",
  justify_content="center",
  font_family="Inter",
)
_STYLE_CHAT_BOX = me.Style(
  flex_grow=1,
  overflow_y="scroll",
  padding=_DEFAULT_PADDING,
  margin=me.Margin(bottom=10),
  border_radius="10px",
)
_STYLE_CHAT_INPUT = me.Style(width="100%",border=me.Border.all(me.BorderSide(style="none")))
_STYLE_CHAT_INPUT_BOX = me.Style(
  padding=me.Padding(top=-1), display="flex", flex_direction="row"
)
_STYLE_UPLOAD_BUTTON = me.Style(margin=me.Margin(top=8, left=8),font_weight="bold",background=me.theme_var("secondary-container"))
_STYLE_CHAT_BUBBLE_NAME = me.Style(
  font_weight="bold",
  font_size="13px",
  padding=me.Padding(left=15, right=15, bottom=5)
)
_STYLE_CHAT_BUBBLE_PLAINTEXT = me.Style(margin=me.Margin.symmetric(vertical=15))
_STYLE_CHAT_MESSAGE_BOX = me.Style(
  display="flex",
  flex_direction="row",
  align_items="center"
)
_COLOR_CHAT_MESSAGE_ICON_BACKGROUND_YOU = "#ff6c6c"
_COLOR_CHAT_MESSAGE_ICON_BACKGROUND_BOT = "#ffbd45"
_STYLE_CHAT_MESSAGE_ICON = me.Style(
  height="25px",
  width="25px",
  margin=me.Margin(top=5)
)
_STYLE_RICH_ELEMENT_BOX = style=me.Style(
  display="flex",
  flex_direction="column",
  gap=15,
  margin=me.Margin.all(15),
)


def _make_style_chat_bubble_wrapper(role: Role) -> me.Style:
  """Generates styles for chat bubble position.

  Args:
    role: Chat bubble alignment depends on the role
  """
  align_items = "start"
  return me.Style(
    display="flex",
    flex_direction="column",
    align_items=align_items,
  )

def _make_chat_bubble_icon_style(role: Role) -> me.Style:
  """Generates styles for chat bubble icon

  Args:
    role: Chat bubble background color depends on the role
  """
  background = (
   _COLOR_CHAT_MESSAGE_ICON_BACKGROUND_YOU if role == _ROLE_USER else _COLOR_CHAT_MESSAGE_ICON_BACKGROUND_BOT
  )
  return me.Style(
    background=background,
    border_radius="10px",
    margin=me.Margin(right=10),
    height="35px",
    width="35px",
    display="flex",
    justify_content="center",
    align_items="center"
  )

def _make_chat_bubble_style(role: Role) -> me.Style:
  """Generates styles for chat bubble.

  Args:
    role: Chat bubble background color depends on the role
  """
  background = (
    _COLOR_CHAT_BUBBLE_YOU if role == _ROLE_USER else _COLOR_CHAT_BUBBLE_BOT
  )
  return me.Style(
    width="100%",
    font_size="16px",
    line_height="1",
    background=background,
    border_radius="15px",
    padding=me.Padding(right=15, left=15, bottom=3),
    margin=me.Margin(bottom=10),
  )


@dataclass(kw_only=True)
class ChatMessage:
  """Chat message metadata."""

  role: Role = "user"
  content: Union[str, Dict[str, Any], None] = ""
  rich_content: Optional[Dict[str, Any]] = field(default_factory=dict)


@me.stateclass
class State:
  input: str
  output: list[ChatMessage]
  in_progress: bool = False
  file: me.UploadedFile

def handle_upload(event: me.UploadEvent):
  state = me.state(State)
  state.file = event.file

def on_blur(e: me.InputBlurEvent):
  state = me.state(State)
  state.input = e.value

def on_newline(e: me.TextareaShortcutEvent):
  state = me.state(State)
  state.input = e.value + "\n"

def on_submit(e: me.TextareaShortcutEvent):
  state = me.state(State)
  state.input = e.value
  state.output = e.value

def on_clear(e: me.TextareaShortcutEvent):
  state = me.state(State)
  state.input = ""
  state.output = ""

def on_chip_click(event: me.ClickEvent):
  state = me.state(State)
  state.input = event.key

def display_citations(citations):
  with me.box(style=me.Style(display="flex", justify_content="flex-start")):
      for i in range(len(citations)):
        with me.card(appearance="raised", style=me.Style(display="inline-block",margin=me.Margin.all(2),background=me.theme_var("secondary-container"))):
            with me.box(style=me.Style(display="flex", justify_content="start", align_items="center")):
              with me.card_content():
                  me.link(
                      text=citations[i]["title"],
                      open_in_new_tab=True,
                      url=citations[i]["url"],
                      style=me.Style(color=me.theme_var("tertiary"), text_decoration="none"),
                  )
              me.icon(icon="open_in_new",style=me.Style(margin=me.Margin(right=2, top=7), font_size=20))

def display_chips(chips):
  # state = me.state(State)
  with me.box(style=me.Style(display="flex", justify_content="flex-start")):
      for i in range(len(chips)):
        # chip_at_turn = int(len(state.output) / 2)
        with me.content_button(type="raised",
                               on_click=on_chip_click,
                              #  key=f"chip_{i}_turn_{chip_at_turn}",
                               key=chips[i]["text"],
                               style=me.Style(border_radius="10px",margin=me.Margin.all(5),background=me.theme_var("secondary-container")
                              )):
          me.text(text=chips[i]["text"])
                  

def display_rich_elements(rich_content):

  if rich_content["type"] == "file":
    # Display file name card
    pass
  elif rich_content["type"] == "image":
    # Display image inside a container
    pass
  elif rich_content["type"] == "chips":
    # Display clickable mini chip that populates the input bar
    return display_chips(rich_content["chips"])
    pass
  elif rich_content["type"] == "citations":
    # Display clickable card that opens a link in new page
    return display_citations(rich_content["citations"])
  else:
    return None

def chat(
  transform: Callable[
    [str, list[ChatMessage]], Generator[str, None, None] | str
  ],
  *,
  title: str | None = None,
  bot_user: str = _BOT_USER_DEFAULT,
):
  """Creates a simple chat UI which takes in a prompt and chat history and returns a
  response to the prompt.

  This function creates event handlers for text input and output operations
  using the provided function `transform` to process the input and generate the output.

  Args:
    transform: Function that takes in a prompt and chat history and returns a response to the prompt.
    title: Headline text to display at the top of the UI.
    bot_user: Name of your bot / assistant.
  """
  state = me.state(State)

  def on_click_submit(e: me.ClickEvent):
    yield from submit()

  def on_input_enter(e: me.InputEnterEvent):
    state = me.state(State)
    state.input = e.value
    yield from submit()
    me.focus_component(key=f"input-{len(state.output)}")
    yield

  def submit():
    state = me.state(State)
    if state.in_progress or not state.input:
      return
    input = state.input
    state.input = ""
    yield

    output = state.output
    if output is None:
      output = []
    output.append(ChatMessage(role=_ROLE_USER, content=input))
    state.in_progress = True
    # me.scroll_into_view(key="end_of_messages")
    yield

    # start_time = time.time()
    output_message = transform(input, state.output)
    assistant_message = ChatMessage(role=_ROLE_ASSISTANT)
    output.append(assistant_message)
    state.output = output
    
    assistant_message.content = output_message["message"]
    assistant_message.rich_content = output_message.get("rich_content")
    
    # TODO: Simulate streaming, currently static dict is passed
    # for content in output_message:
    #   assistant_message.content += content
    #   # TODO: 0.25 is an abitrary choice. In the future, consider making this adjustable.
    #   if (time.time() - start_time) >= 0.25:
    #     start_time = time.time()
    #     yield
    state.in_progress = False
    me.focus_component(key=f"input-{len(state.output)}")
    me.scroll_into_view(key="end_of_messages")
    yield

  def toggle_theme(e: me.ClickEvent):
    if me.theme_brightness() == "light":
      me.set_theme_mode("dark")
    else:
      me.set_theme_mode("light")

  with me.box(style=_STYLE_APP_CONTAINER):

    if title:
      with me.box(
            style=me.Style(
            display="flex", flex_direction="row",justify_content= "center", margin=me.Margin(right=10),
        )):
        me.text(title, type="headline-3", style=_STYLE_TITLE)
        # TODO: Make title as linear gradient
        # me.html(html=f"""
        #         <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet">
        #         <h3 style='background: linear-gradient(90deg, #5E60CE 0%, #FF6B6B 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: bold; font-family: Inter; font-size: 30px; white-space: nowrap;'>
        #         {title}</h3>""",
        #         mode="sandboxed")
        with me.content_button(
          type="icon",
          style=me.Style(margin=me.Margin(top=6)),
          on_click=toggle_theme,
        ):
          me.icon("light_mode" if me.theme_brightness() == "dark" else "dark_mode")
        

    with me.box(style=_STYLE_CHAT_BOX):
      for msg in state.output:
        with me.box(style=_make_style_chat_bubble_wrapper(msg.role)):
          with me.box(style=_make_chat_bubble_style(msg.role)):
            if msg.role == _ROLE_USER:
              with me.box(style=_STYLE_CHAT_MESSAGE_BOX):
                    with me.box(style=_make_chat_bubble_icon_style(msg.role)):
                        me.icon("face", style=_STYLE_CHAT_MESSAGE_ICON)
                    me.markdown(msg.content)
            else:
              with me.box(style=_STYLE_CHAT_MESSAGE_BOX):
                    with me.box(style=_make_chat_bubble_icon_style(msg.role)):
                        me.icon("smart_toy", style=_STYLE_CHAT_MESSAGE_ICON)
                    if msg.rich_content:
                      with me.box(style=_STYLE_RICH_ELEMENT_BOX):
                        with me.box():
                            me.markdown(msg.content)
                        display_rich_elements(msg.rich_content)
                    else:
                      me.markdown(msg.content)

      with me.box(key="end_of_messages", style=me.Style(height=1)):
        pass

    with me.box(style=_STYLE_CHAT_INPUT_BOX):
      with me.box(style=me.Style(flex_grow=1)):
        me.textarea(
          label=_LABEL_INPUT,
          key=f"input-{len(state.output)}",
          value=state.input,
          on_blur=on_blur,
          shortcuts={
            me.Shortcut(key="enter"): on_input_enter,
            me.Shortcut(shift=True, key="ENTER"): on_newline,
            me.Shortcut(shift=True, meta=True, key="Enter"): on_clear,
          },
          appearance="outline",
          style=_STYLE_CHAT_INPUT,
          color="primary",
          placeholder=_LABEL_INPUT,
          rows=2,
          autosize=True,
          max_rows=5
        )

      with me.content_uploader(
        accepted_file_types=ACCEPTED_FILE_TYPES,
        on_upload=handle_upload,
        type="raised",
        style=_STYLE_UPLOAD_BUTTON,
        color="accent",
        disabled=state.in_progress
      ):
        me.icon(
          _LABEL_BUTTON_IN_PROGRESS if state.in_progress else _LABEL_BUTTON
        )
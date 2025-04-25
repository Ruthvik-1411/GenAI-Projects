"""Components for mesop chat box"""
# import time
import mesop as me
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any, Callable, Generator, Literal
from mesop_components.copy_to_clipboard.copy_to_clipboard_component import copy_to_clipboard_component

Role = Literal["user", "assistant"]
ACCEPTED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf","video/mp4"]

_ROLE_USER = "user"
_ROLE_ASSISTANT = "assistant"
_BOT_USER_DEFAULT = "assistant"

_COLOR_BACKGROUND = me.theme_var("background")
_COLOR_CHAT_BUBBLE_YOU = me.theme_var("surface")
_COLOR_CHAT_BUBBLE_BOT = me.theme_var("surface-container-low")

_DEFAULT_PADDING = me.Padding.all(5)

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
_STYLE_CHAT_INPUT = me.Style(
  background=me.theme_var("surface-container"),
  border=me.Border.all(me.BorderSide(style="none"),),
  color=me.theme_var("on-surface-variant"),
  outline="none",
  overflow_y="auto",
  padding=me.Padding(top=16, left=16),
  width="100%",
)
_STYLE_CHAT_INPUT_BOX = me.Style(
  background=me.theme_var("surface-container"),
  border_radius=16,
  display="flex",
  margin=me.Margin(bottom=8),
  padding=me.Padding.all(8),
)
_STYLE_UPLOAD_BUTTON = me.Style(margin=me.Margin(top=8, left=8),font_weight="bold")

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
  diagnostic_info: Optional[Dict[str, Any]] = field(default_factory=dict)


@me.stateclass
class State:
  input: str
  output: list[ChatMessage]
  in_progress: bool = False
  file: me.UploadedFile
  open_dialog_id: str | None = None

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

def on_click_close_background(e: me.ClickEvent):
  state = me.state(State)
  if e.is_target:
    state.open_dialog_id = None

def on_click_close_dialog(e: me.ClickEvent):
  state = me.state(State)
  state.open_dialog_id = None

def on_click_dialog_open(e: me.ClickEvent):
  state = me.state(State)
  state.open_dialog_id = e.key

@me.content_component
def dialog(*, is_open: bool, on_click_background: Callable | None = None):
  with me.box(
    style=me.Style(
      background="rgba(0, 0, 0, 0.4)"
      if me.theme_brightness() == "light" else "rgba(255, 255, 255, 0.4)",
      display="block" if is_open else "none",
      height="100%",
      position="fixed",
      top=0,
      left=0,
      width="100%",
      z_index=1000,
    ),
  ):
    with me.box(
      on_click=on_click_background,
      style=me.Style(
        place_items="center",
        display="grid",
        height="100%",
      ),
    ):
      with me.box(
        style=me.Style(
          background=me.theme_var("surface-container-lowest"),
          border_radius=20,
          box_sizing="content-box",
          margin=me.Margin.symmetric(vertical="0", horizontal="auto"),
          padding=me.Padding.all(20),
        )
      ):
        me.slot()

@me.content_component
def dialog_actions():
  """Helper component for rendering action buttons so they are right aligned.

  This component is optional. If you want to position action buttons differently,
  you can just write your own Mesop markup.
  """
  with me.box(
    style=me.Style(
      display="flex", justify_content="end", gap=5, margin=me.Margin(top=20)
    )
  ):
    me.slot()

def display_citations(citations):
  with me.box(style=me.Style(display="flex", justify_content="flex-start")):
      for i in range(len(citations)):
        with me.card(appearance="raised", style=me.Style(display="inline-block",margin=me.Margin.all(2),background=me.theme_var("secondary-container"))):
            with me.box(style=me.Style(display="flex", justify_content="start", align_items="center")):
              with me.card_content():
                # FIXME: citation url tries to navigate to a page of mesop app
                # local url starts with /home/user/...pdf. When opened in browser, browser opens it as file:///home/user/...pdf
                # But when this url is displayed on UI, when opened, it opens as localhost:port/home/user/...pdf
                # Since localhost is serving mesop and not pdf files, it's a broken url
                # HOTFIX: serve the document/ folder as python http server and replace the url to hit this server.
                me.link(
                    text=citations[i]["title"],
                    open_in_new_tab=True,
                    # url=citations[i]["url"],
                    url="http://0.0.0.0:8000/"+citations[i]["url"].split("/")[-1],
                    style=me.Style(color=me.theme_var("tertiary"), text_decoration="none"),
                )
              me.icon(icon="open_in_new",style=me.Style(margin=me.Margin(right=2, top=7), font_size=20))

def display_chips(chips):
  """Display chip buttons to auto populate chip text in input area"""
  with me.box(style=me.Style(display="flex", justify_content="flex-start")):
      for i in range(len(chips)):
        with me.content_button(type="raised",
                               on_click=on_chip_click,
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
    # Display clickable mini chip that populates the input text area
    return display_chips(rich_content["chips"])
    pass
  elif rich_content["type"] == "citations":
    # Display clickable card that opens a link in new page
    return display_citations(rich_content["citations"])
  else:
    return None

def display_helper_buttons(message, message_index):
  state = me.state(State)
  dialog_id = f"dialog_{message_index}"

  with me.box(style=me.Style(
    display="flex",
    flex_direction="row-reverse",
    align_items="center"
    )):
      with dialog(
        is_open=(state.open_dialog_id == dialog_id),
        on_click_background=on_click_close_background,
      ):
        with me.box(style=me.Style(
            display="flex",
            flex_direction="row",
            align_items="center",
            justify_content="space-between"
        )):
          me.text("Diagnostic Info", type="headline-5")
          with copy_to_clipboard_component(text=message.diagnostic_info):
            with me.content_button(type="icon"):
              me.icon("content_copy")
        with me.box(
          style=me.Style(
            overflow_y="auto",
            max_height="360px",
            max_width="720px",
            background=me.theme_var("surface"),
            border_radius=10,
            padding=me.Padding.all(10),
            font_family="monospace",
            font_size="14px",
            white_space="pre-wrap",
            word_wrap="break-word"
          )
        ):
          me.markdown(message.diagnostic_info)
          # TODO: Add a copy button or use markdown for code
          # me.markdown("```json"+message.diagnostic_info+"```")
        with dialog_actions():
          me.button("Close", on_click=on_click_close_dialog)
      with me.content_button(type="icon",on_click=on_click_dialog_open, key=dialog_id):
        me.icon("assignment")
      with copy_to_clipboard_component(text=message.content):
        with me.content_button(type="icon"):
          me.icon("content_copy")

def chat(
  transform: Callable[
    [str, list[ChatMessage]], Generator[str, None, None] | str
  ],
  *,
  title: str | None = None,
  bot_user: str = _BOT_USER_DEFAULT,
  reset: bool = False
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

  if reset:
      state.output = []

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
    assistant_message.diagnostic_info = output_message.get("diagnostic_info")
    
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
      for index, msg in enumerate(state.output):
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
            if msg.diagnostic_info:
              display_helper_buttons(msg, index)
      with me.box(key="end_of_messages", style=me.Style(height=1)):
        pass

    with me.box(style=_STYLE_CHAT_INPUT_BOX):
      with me.box(style=me.Style(flex_grow=1)):
        me.native_textarea(
          key=f"input-{len(state.output)}",
          value=state.input,
          on_blur=on_blur,
          shortcuts={
            me.Shortcut(key="enter"): on_input_enter,
            me.Shortcut(shift=True, key="ENTER"): on_newline,
            me.Shortcut(shift=True, meta=True, key="Enter"): on_clear,
          },
          style=_STYLE_CHAT_INPUT,
          placeholder=_LABEL_INPUT,
          autosize=True,
          min_rows=5,
          max_rows=10
        )

      with me.content_uploader(
        accepted_file_types=ACCEPTED_FILE_TYPES,
        on_upload=handle_upload,
        style=_STYLE_UPLOAD_BUTTON,
        disabled=state.in_progress
      ):
        me.icon(
          _LABEL_BUTTON_IN_PROGRESS if state.in_progress else _LABEL_BUTTON
        )
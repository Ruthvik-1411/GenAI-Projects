"""Mesop copy to clipboard component"""
import mesop as me

@me.web_component(path="./copy_to_clipboard_component.js")
def copy_to_clipboard_component(
  *,
  text: str = "",
  key: str | None = None,
):
    """Copy to clipboard web component"""
    return me.insert_web_component(
      name="copy-to-clipboard-component",
      key=key,
      properties={
        "text": text,
      },
    )

wwwidget Todo
==============
- Take the Internet Connection from the Bluetooth
- Lock up if Bluetooth Device isn't nearby (alternatively RFID?)
- Formatting boxes using UTF-8 box drawing characters
- Coloring / Bold / Italic of the text output
- Capture mouse clicks on certain widgets
- Show "fullscreen editions" of widgets after mouseclicks
- Show several screens
- Adapt the queue architecture a bit:
  - To send stuff from the main controller to the separate widgets: every widget has it's own queue
  - To receive stuff from the different widgets: one queue for all the widgets is enough

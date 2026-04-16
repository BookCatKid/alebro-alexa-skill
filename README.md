# Label Maker Alexa Skill

An Alexa skill that controls a label maker over MQTT. You can print labels and check printer status using voice commands.

## ⚠️ Important

This skill requires a companion backend running on a Raspberry Pi that listens for MQTT messages and drives the label printer. **The backend code is not publicly released at this time**, so this skill will not function on its own.

## Setup

1. Copy `lambda/config.py.example` to `lambda/config.py` and fill in your MQTT credentials.
2. Deploy the skill through the Alexa Developer Console.

## Voice Commands

- *"Alexa, open label maker"* – Launch the skill
- *"Print hello world"* – Print a label with the given message
- *"What's the status"* – Check if the label maker is online

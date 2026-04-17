import logging
import time

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
)
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import get_supported_interfaces
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective
import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    WEB_UI_URL,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


APL_SIMPLE = {
    "type": "APL",
    "version": "1.6",
    "import": [{"name": "alexa-layouts", "version": "1.7.0"}],
    "mainTemplate": {
        "parameters": ["payload"],
        "items": [
            {
                "type": "Container",
                "width": "100vw",
                "height": "100vh",
                "alignItems": "center",
                "justifyContent": "center",
                "items": [
                    {
                        "type": "Text",
                        "text": "${payload.data.properties.title}",
                        "fontSize": "5vh",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "paddingLeft": "5vw",
                        "paddingRight": "5vw",
                    },
                    {
                        "type": "Text",
                        "text": "${payload.data.properties.subtitle}",
                        "fontSize": "3vh",
                        "textAlign": "center",
                        "opacity": 0.7,
                        "paddingTop": "3vh",
                        "paddingLeft": "5vw",
                        "paddingRight": "5vw",
                    },
                ],
            }
        ],
    },
}

APL_CONFIRM = {
    "type": "APL",
    "version": "1.6",
    "import": [{"name": "alexa-layouts", "version": "1.7.0"}],
    "mainTemplate": {
        "parameters": ["payload"],
        "items": [
            {
                "type": "Container",
                "width": "100vw",
                "height": "100vh",
                "direction": "column",
                "alignItems": "center",
                "justifyContent": "center",
                "items": [
                    {
                        "type": "Text",
                        "text": "Print this label?",
                        "fontSize": "4vh",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "paddingBottom": "3vh",
                    },
                    {
                        "type": "Container",
                        "width": "80vw",
                        "borderWidth": 2,
                        "borderColor": "white",
                        "borderRadius": "2vh",
                        "padding": "4vh",
                        "alignItems": "center",
                        "items": [
                            {
                                "type": "Text",
                                "text": "${payload.data.properties.message}",
                                "fontSize": "4vh",
                                "textAlign": "center",
                                "color": "#00CAFF",
                            }
                        ],
                    },
                    {
                        "type": "Container",
                        "direction": "row",
                        "paddingTop": "3vh",
                        "items": [
                            {
                                "type": "TouchWrapper",
                                "onPress": {
                                    "type": "SendEvent",
                                    "arguments": ["lowercase"],
                                },
                                "item": {
                                    "type": "Frame",
                                    "borderRadius": "2vh",
                                    "backgroundColor": "#FF8800",
                                    "padding": "2vh",
                                    "paddingLeft": "3vw",
                                    "paddingRight": "3vw",
                                    "items": [
                                        {
                                            "type": "Text",
                                            "text": "Aa",
                                            "fontSize": "3vh",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                        }
                                    ],
                                },
                            },
                            {"type": "Container", "width": "3vw"},
                            {
                                "type": "TouchWrapper",
                                "onPress": {
                                    "type": "OpenURL",
                                    "url": WEB_UI_URL,
                                },
                                "item": {
                                    "type": "Frame",
                                    "borderRadius": "2vh",
                                    "backgroundColor": "#5555FF",
                                    "padding": "2vh",
                                    "paddingLeft": "3vw",
                                    "paddingRight": "3vw",
                                    "items": [
                                        {
                                            "type": "Text",
                                            "text": "🌐 Web",
                                            "fontSize": "3vh",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                        }
                                    ],
                                },
                            },
                            {"type": "Container", "width": "3vw"},
                            {
                                "type": "TouchWrapper",
                                "onPress": {
                                    "type": "SendEvent",
                                    "arguments": ["retry"],
                                },
                                "item": {
                                    "type": "Frame",
                                    "borderRadius": "2vh",
                                    "backgroundColor": "#DD2222",
                                    "padding": "2vh",
                                    "paddingLeft": "3vw",
                                    "paddingRight": "3vw",
                                    "items": [
                                        {
                                            "type": "Text",
                                            "text": "🔄 Retry",
                                            "fontSize": "3vh",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                        }
                                    ],
                                },
                            },
                            {"type": "Container", "width": "3vw"},
                            {
                                "type": "TouchWrapper",
                                "onPress": {
                                    "type": "SendEvent",
                                    "arguments": ["confirm"],
                                },
                                "item": {
                                    "type": "Frame",
                                    "borderRadius": "2vh",
                                    "backgroundColor": "#22AA22",
                                    "padding": "2vh",
                                    "paddingLeft": "3vw",
                                    "paddingRight": "3vw",
                                    "items": [
                                        {
                                            "type": "Text",
                                            "text": "✅ Print",
                                            "fontSize": "3vh",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                        }
                                    ],
                                },
                            },
                        ],
                    },
                ],
            }
        ],
    },
}


def supports_apl(handler_input):
    supported = get_supported_interfaces(handler_input)
    return supported.alexa_presentation_apl is not None


def show_screen(handler_input, title, subtitle=""):
    if supports_apl(handler_input):
        handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token="mainScreen",
                document=APL_SIMPLE,
                datasources={
                    "data": {
                        "type": "object",
                        "properties": {"title": title, "subtitle": subtitle},
                    }
                },
            )
        )


def show_confirm_screen(handler_input, message):
    if supports_apl(handler_input):
        handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token="confirmScreen",
                document=APL_CONFIRM,
                datasources={
                    "data": {"type": "object", "properties": {"message": message}}
                },
            )
        )


def _mqtt_request(publish_topic, publish_payload, subscribe_topic, timeout_seconds=5):
    response_message = {"value": None}

    def on_connect(client, userdata, flags, rc):
        logger.info(f"MQTT connected (rc={rc})")
        client.subscribe(subscribe_topic)
        client.publish(publish_topic, publish_payload)

    def on_message(client, userdata, msg):
        response_message["value"] = msg.payload.decode()
        client.disconnect()

    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    client.loop_start()
    deadline = time.time() + timeout_seconds
    while response_message["value"] is None and time.time() < deadline:
        time.sleep(0.1)
    client.loop_stop()

    return response_message["value"]


def get_status_from_pi():
    return _mqtt_request("simon/test", "status", "simon/response", timeout_seconds=3)


def send_print_message(message):
    return _mqtt_request(
        "simon/print", message, "simon/print/response", timeout_seconds=6
    )


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Label maker ready. You can say print followed by a message, or ask for the status."
        show_screen(
            handler_input,
            "🏷️ Label Maker",
            'Say "print" followed by a message, or ask for the status.',
        )
        return (
            handler_input.response_builder.speak(speak_output)
            .ask("What would you like to print?")
            .response
        )


class PrintMessageIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("PrintMessageIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        message = slots["message"].value if "message" in slots else None

        if not message:
            show_screen(handler_input, "🏷️ Label Maker", "What message should I print?")
            return (
                handler_input.response_builder.speak("What message should I print?")
                .ask("Tell me what to print.")
                .response
            )

        capitalized = " ".join(word.capitalize() for word in message.split())
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["pending_message"] = capitalized
        session_attr["case_state"] = "title"

        speak_output = f'I heard: "{capitalized}". Should I print that? Say yes or no.'
        show_confirm_screen(handler_input, capitalized)
        return (
            handler_input.response_builder.speak(speak_output)
            .ask("Say yes to print, or no to try again.")
            .response
        )


def _do_print(handler_input, message):
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr["last_printed"] = message
    response = send_print_message(message)
    if response:
        show_screen(handler_input, "✅ Sent!", f'"{message}"')
        return handler_input.response_builder.speak(response).response
    else:
        show_screen(handler_input, "⚠️ No Response", f'Sent: "{message}"')
        return handler_input.response_builder.speak(
            "I sent the message, but the label maker didn't respond."
        ).response


def _do_retry(handler_input):
    show_screen(handler_input, "🏷️ Label Maker", 'Say "print" followed by your message.')
    return (
        handler_input.response_builder.speak("OK, what would you like to print?")
        .ask("Tell me what to print.")
        .response
    )


class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        message = session_attr.get("pending_message")

        if not message:
            show_screen(
                handler_input, "🏷️ Label Maker", 'Say "print" followed by your message.'
            )
            return (
                handler_input.response_builder.speak(
                    "There's nothing to confirm. Say print followed by a message."
                )
                .ask("What would you like to print?")
                .response
            )

        session_attr.pop("pending_message", None)
        return _do_print(handler_input, message)


class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr.pop("pending_message", None)
        return _do_retry(handler_input)


class TouchEventHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("Alexa.Presentation.APL.UserEvent")(
            handler_input
        )

    def handle(self, handler_input):
        args = list(handler_input.request_envelope.request.arguments)
        session_attr = handler_input.attributes_manager.session_attributes

        if args and args[0] == "confirm":
            message = session_attr.pop("pending_message", None)
            if message:
                return _do_print(handler_input, message)
        elif args and args[0] == "retry":
            session_attr.pop("pending_message", None)
            return _do_retry(handler_input)
        elif args and args[0] in ("lowercase", "toggle_case"):
            message = session_attr.get("pending_message")
            if message:
                current_state = session_attr.get("case_state", "title")
                if current_state == "title":
                    case_state = "lower"
                    new_msg = message.lower()
                elif current_state == "lower":
                    case_state = "upper"
                    new_msg = message.upper()
                else:
                    case_state = "title"
                    new_msg = " ".join(word.capitalize() for word in message.split())
                session_attr["pending_message"] = new_msg
                session_attr["case_state"] = case_state
                show_confirm_screen(handler_input, new_msg)
                return (
                    handler_input.response_builder.speak(f"Switched to: {new_msg}")
                    .ask("Say yes to print, or no to cancel.")
                    .response
                )

        return handler_input.response_builder.speak("Something went wrong.").response


class ReprintIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ReprintIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        message = session_attr.get("last_printed")

        if not message:
            show_screen(handler_input, "🏷️ Label Maker", "Nothing to reprint.")
            return (
                handler_input.response_builder.speak(
                    "There's nothing to reprint. Say print followed by a message first."
                )
                .ask("What would you like to print?")
                .response
            )

        capitalized = " ".join(word.capitalize() for word in message.split())
        session_attr["pending_message"] = capitalized
        session_attr["case_state"] = "title"
        speak_output = f'Reprint: "{capitalized}". Should I print that? Say yes or no.'
        show_confirm_screen(handler_input, capitalized)
        return (
            handler_input.response_builder.speak(speak_output)
            .ask("Say yes to print, or no to cancel.")
            .response
        )


class StatusIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("StatusIntent")(handler_input)

    def handle(self, handler_input):
        status = get_status_from_pi()

        if status:
            speak_output = f"The label maker is {status}."
            show_screen(handler_input, "🟢 Status", status.capitalize())
        else:
            speak_output = "The label maker didn't respond."
            show_screen(handler_input, "🔴 Offline", "The label maker didn't respond.")

        return handler_input.response_builder.speak(speak_output).response


class OpenWebIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("OpenWebIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Opening the Alebro web interface."
        if supports_apl(handler_input):
            handler_input.response_builder.add_directive(
                {
                    "type": "Alexa.Presentation.APL.OpenURL",
                    "url": WEB_UI_URL,
                    "windowId": "dialog",
                }
            )
        return handler_input.response_builder.speak(speak_output).response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "You can ask me to print a label by saying print followed by your message. "
            "You can also ask for the label maker status."
        )
        show_screen(handler_input, "❓ Help", '"Print [message]" or "Status"')
        return (
            handler_input.response_builder.speak(speak_output)
            .ask("What would you like to print?")
            .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(
            handler_input
        ) or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Goodbye!").response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speech = "I didn't understand that. You can say print followed by a message, or ask for the status."
        show_screen(
            handler_input,
            "🏷️ Label Maker",
            'Say "print" followed by a message, or ask for the status.',
        )
        return (
            handler_input.response_builder.speak(speech)
            .ask("What would you like to do?")
            .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        return (
            handler_input.response_builder.speak(
                "Sorry, something went wrong. Please try again."
            )
            .ask("What would you like to do?")
            .response
        )


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PrintMessageIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(TouchEventHandler())
sb.add_request_handler(ReprintIntentHandler())
sb.add_request_handler(StatusIntentHandler())
sb.add_request_handler(OpenWebIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()

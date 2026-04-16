import logging
import time

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.dispatch_components import AbstractExceptionHandler, AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_model import Response
import paho.mqtt.client as mqtt

from config import MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME, MQTT_PASSWORD

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    return _mqtt_request("simon/print", message, "simon/print/response", timeout_seconds=6)


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Label maker ready. You can say print followed by a message, or ask for the status."
        return (
            handler_input.response_builder
                .speak(speak_output)
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
            return (
                handler_input.response_builder
                    .speak("What message should I print?")
                    .ask("Tell me what to print.")
                    .response
            )

        response = send_print_message(message)
        speak_output = response if response else "I sent the message, but the label maker didn't respond."

        return handler_input.response_builder.speak(speak_output).response


class StatusIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("StatusIntent")(handler_input)

    def handle(self, handler_input):
        status = get_status_from_pi()
        speak_output = f"The label maker is {status}." if status else "The label maker didn't respond."
        return handler_input.response_builder.speak(speak_output).response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "You can ask me to print a label by saying print followed by your message. "
            "You can also ask for the label maker status."
        )
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("What would you like to print?")
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Goodbye!").response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speech = "I didn't understand that. You can say print followed by a message, or ask for the status."
        return handler_input.response_builder.speak(speech).ask("What would you like to do?").response


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
            handler_input.response_builder
                .speak("Sorry, something went wrong. Please try again.")
                .ask("What would you like to do?")
                .response
        )


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PrintMessageIntentHandler())
sb.add_request_handler(StatusIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()

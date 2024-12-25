from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils
import requests
import logging
import json
import random

# Set your OpenAI API key
api_key = "your_openai_api_key"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "What's up?"

        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["chat_history"] = []
        return (
            handler_input.response_builder
                .speak(f"<voice name='Salli'>{speak_output}</voice>")
                .ask(f"<voice name='Salli'>{speak_output}</voice>")
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for Gpt Query Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        query = handler_input.request_envelope.request.intent.slots["query"].value
        
        # if response to "anything else?" is exactly "no"
        if query and query.strip().lower() == "no":
            speak_output = get_goodbye_phrase()
            return (
                handler_input.response_builder
                    .speak(f"<voice name='Salli'>{speak_output}</voice>")
                    .set_should_end_session(True)  # End the session
                    .response
            )

        session_attr = handler_input.attributes_manager.session_attributes
        if "chat_history" not in session_attr:
            session_attr["chat_history"] = []
        response = generate_gpt_response(session_attr["chat_history"], query)
        session_attr["chat_history"].append((query, response))

        return (
                handler_input.response_builder
                    .speak(f"<voice name='Salli'>{response}</voice>")
                    .ask(f"<voice name='Salli'>Anything else?</voice>")
                    .response
            )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Fast pass is broken, something went wrong, check them logs"

        return (
            handler_input.response_builder
                .speak(f"<voice name='Salli'>{speak_output}</voice>")
                .ask(f"<voice name='Salli'>{speak_output}</voice>")
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = get_goodbye_phrase()
        return (
            handler_input.response_builder
                .speak(f"<voice name='Salli'>{speak_output}</voice>")
                .response
        )

def get_goodbye_phrase():
    goodbye_phrases = [
        "Cool cool, see ya next time",
        "Okay, see ya",
        "Until next time, take care!",
        "Peace out, see you soon!",
    ]
    return random.choice(goodbye_phrases)

def generate_gpt_response(chat_history, new_question):
    """Generates a GPT response to a new question"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    url = "https://api.openai.com/v1/chat/completions"
    messages = [{"role": "system", "content": "You are a helpful assistant that prioritizes answering in one sentence."}]
    for question, answer in chat_history[-50:]:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})
    messages.append({"role": "user", "content": new_question})
    
    data = {
        "model": "gpt-4o",
        "messages": messages,
        # "max_tokens": 300,
        # "temperature": 0.5
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()
        if response.ok:
            return response_data['choices'][0]['message']['content']
        else:
            return f"Error {response.status_code}: {response_data['error']['message']}"
    except Exception as e:
        return f"Error generating response: {str(e)}"

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
from __future__ import print_function

import json
import urllib
import boto3


sqs_client = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

DEBUG = True

def lambda_handler(event, context):

    print("Loaded Application with ID=" + event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    print("Session started with id=" + session['sessionId'])
   

    return


def on_launch(launch_request, session):
    print("Application statrted with requestId=" + launch_request['requestId'] + ", sessionId=" + session['sessionId'])
    try:
        state = restore(session)
    except Exception:
        state = None
    if state is not None:
        restore_unity(state,session)
        return build_response({}, build_speechlet_response("Restore", 
                "Your previous session has been restored!", 
                "You can ask me for information about any of the objects in the solar system, ", 
                False))
    return get_welcome_response()


def on_intent(intent_request, session):
    intent = intent_request['intent']
    return process_intent(intent,session)



def on_session_ended(session_ended_request, session):
    print("Session ended for id=" + session['sessionId'])
 

# --------------- Functions that control the skill's behavior ------------------

def process_intent(intent, session):
    if intent is None:
        return get_exception_response("")



    try:
        intent_name = intent['name']
        if intent_name == "Repeat":
            retrived_intent = retrive_state(session)
            return process_intent(retrived_intent,session)
        elif intent_name == "CelestialObjectsAge":
            return build_response({}, build_speechlet_response("Age", 
                "The solar system and everything within it is 4.6 Billion Years Old.", 
                "You can ask me for information about any of the objects in the solar system, ", 
                False))
        elif intent_name == "AMAZON.HelpIntent":
            return get_welcome_response()
        elif intent_name == "AMAZON.CancelIntent":
            return get_cancel_response()
        elif intent_name == "planetDescription":
            return describe_planet(intent, session)
        elif intent_name == "planetRadius":
            return describe_size(intent,session)
        elif intent_name == "planetWeight":
            return describe_mass(intent,session)
        elif intent_name == "planetDistance":
            return describe_distance(intent,session)
        elif intent_name == "planetNumberOfMoons":
            return describe_moons(intent,session)
        elif intent_name == "discribeObjectNotPlanet":
            return describe_object(intent,session)
        elif intent_name == "CelestialObjectsDescription":
            return describe_item(intent,session)
        elif intent_name == "planetMoonsInformation":
            return detail_moons(intent,session)
        elif intent_name == "planetPeriod":
            return describe_period(intent,session)
        elif intent_name == "planetRotation":
            return describe_rotation(intent,session)
        elif intent_name == "planetDisplay":
            return display_planet(intent,session)
        elif intent_name == "Exit":
            exitIntent(session)
            return build_response({}, build_speechlet_response("Exit", 
                "Please say \"Exit\" to end the session.", 
                "Please say \"Exit\" to end the session.", 
                False))
        else:
            raise ValueError("Invalid intent")
    except Exception as e:
        return get_exception_response(e)

def get_welcome_response():

    card_title = "Virtual Space Tour"
    speech_output = "welcome to your personalized space tour," \
                    "You can ask me for information about any of the objects in the solar system, " 
  
    reprompt_text = "You can ask me more about the planets or the solar system by saying, " \
                    "display the planet Earth."
    should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_exception_response(e):

    card_title = "Virtual Space Tour-Exception"
    speech_output = "Sorry, I don't know the answer to that question or can not perform this action"

    if DEBUG:
        speech_output += str(e)
  
    reprompt_text = "You can ask me more about the planets or the solar system by saying, " \
                    "display the planet Earth."
    should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def exitIntent(session):
    #cleanup 
    table = dynamodb.Table('states')
    table.delete_item(
        Key={
         'session': session['user']['userId']
        }

    )


# --------------- SQS functions to store/retrive state and send messages ----------------------
def send_message( planet):
    sqs_client.send_message(QueueUrl = "https://sqs.us-east-1.amazonaws.com/344524627200/Alexa-UnityCloudBridge",
    MessageBody = build_message(planet))

def build_message(planet):
   message = '{ \"target\": \"' + planet + '\" }'
   return message
# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def store_state(object_name, session, intent):
    table = dynamodb.Table('states')
    table.delete_item(
        Key={
         'session': session['user']['userId'],
        }

    )
    table.put_item(
        Item={
            'session': session['user']['userId'],
            'intent':json.dumps(intent), 
            'object': object_name
         }
    )

def retrive_state(session):
    table = dynamodb.Table('states')
    response = None
    try:
        response = table.get_item(
            Key={
            'session': session['user']['userId']
            }
        )
    except Exception:
        return None

    return json.loads(response['Item']['intent'])

def restore(session):
    table = dynamodb.Table('states')
    response = None
    try:
        response = table.get_item(
            Key={
            'session': session['user']['userId']
            }
        )
    except Exception:
        return None

    return response['Item']['object']

def generate_cancel_response(intent, session):
    session_attributes = {}
    card_title = ""
    speech_output = "Cancelling session. "
    reprompt_text = ""
                    
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_response(intent, session, type):
    planet = intent['slots'][type]['value'].lower()
    if not (planet == 'this planet' or planet == 'this object'):
        store_state(planet, session, intent)

    if planet == 'this planet' or planet == 'this object':
        table = dynamodb.Table('states')
        response = table.get_item(
            Key={
            'session': session['user']['userId']
            }
        )
        planet = response['Item']['object']

    table = dynamodb.Table(type + 's')
    response = table.get_item(
        Key={
            'name': planet
        }
    )

    return response

# --------------- Describe a PLANET Intents ----------------------

def describe_planet( intent, session ):
    planet = get_response(intent, session, 'planet')['Item']
    planet_name = planet['name']
    speech_output = planet['info']

    card_title = planet_name + " Description"
    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe the" + planet_name + " or tell me more about " +planet_name+ "."
                    
    should_end_session = False
    send_message(str(planet['index']))
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def describe_size(intent,session):
    
    planet = get_response(intent, session,'planet')['Item']
    planet_name = planet['name']
    radius = str(planet['size'])
    speech_output = "The radius of " + planet_name + " is " + radius + " Kilometers"

    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe " + planet_name + " or tell me more about " +planet_name+ "."
    card_title = planet_name + " Size"                             
    should_end_session = False
    send_message(str(planet['index']))
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))    

def describe_mass(intent,session):
    
    planet = get_response(intent, session,'planet')['Item']
    planet_name = planet['name']
    mass = str(planet['weight'])
    speech_output = "The mass of " + planet_name + " is " + mass + " Kilograms"

    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe " + planet_name + " or tell me more about " +planet_name+ "."
    card_title = planet_name + " Mass"                             
    should_end_session = False
    send_message(str(planet['index']))
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))   

def describe_distance(intent,session):
    
    planet = get_response(intent, session,'planet')['Item']
    planet_name = planet['name']
    distace = str(planet['distance'])
    speech_output = "The distance of " + planet_name + " from sun is " + distace + " AU"

    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe " + planet_name + " or tell me more about " +planet_name+ "."
    card_title = planet_name + " Distance"                             
    should_end_session = False
    send_message(str(planet['index']))
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))   

def describe_moons(intent,session):
    
    planet = get_response(intent, session,'planet')['Item']
    planet_name = planet['name']
    moons = planet['moons']
    if moons == 1:
        speech_output = planet_name + " has only " + str(moons) + " moon"
    else:
        speech_output = planet_name + " has " + str(moons) + " moons"

    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe " + planet_name + " or tell me more about " +planet_name+ "."
    card_title = planet_name + " Moons"                             
    should_end_session = False
    send_message(str(planet['index']))
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))   

def detail_moons(intent,session):
    planet = get_response(intent, session,'moon')['Item']
    planet_name = planet['name']
    speech_output = planet['info']

    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe " + planet_name + " or tell me more about " +planet_name+ "."
    card_title = planet_name + " Moons Describe"                             
    should_end_session = False
    
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))   


def describe_period(intent,session):
    planet = get_response(intent, session,'planet')['Item']
    planet_name = planet['name']
    earth_days = 365.26
    days = float(planet['period'])
    speech_output = planet_name + " orbits the sun in " + str(days) + " days, which is about " + str("{0:.2f}".format(days/earth_days)) + " years"

    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe " + planet_name + " or tell me more about " +planet_name+ "."
    card_title = planet_name + " Period"                             
    should_end_session = False
    send_message(str(planet['index']))
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))   

def describe_rotation(intent,session):
    planet = get_response(intent, session,'planet')['Item']
    planet_name = planet['name']
    time = planet['rotation']
    speech_output = "A day on " + planet_name + " is about " + str(time) + " earth days"

    if planet_name == "earth":
        speech_output += " ,its kind of obvious"

    reprompt_text = "You can ask me to display another object or ask me for details about" + planet_name + " by saying, " \
                    "describe " + planet_name + " or tell me more about " +planet_name+ "."
    card_title = planet_name + " Period"                             
    should_end_session = False
    send_message(str(planet['index']))
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))   

# --------------- Describe OBJECT Intents ----------------------

def describe_object( intent, session ):
    stellar_object = get_response(intent, session, 'object')['Item']
    object_name = stellar_object['name']
    speech_output = stellar_object['info']

    card_title = object_name + " Description"
    reprompt_text = "You can ask me to display another object or ask me for details about" + object_name + " by saying, " \
                    "describe " + object_name + " or tell me more about " +object_name+ "."

    send_message(str(stellar_object['index']))   
    should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def describe_item( intent, session ):
    name = intent['slots']['item']['value'].lower()
    if not name.endswith('s'):
        intent['slots']['item']['value'] = name + "s"

    stellar_object = get_response(intent, session, 'item')['Item']
    object_name = stellar_object['name']
    speech_output = stellar_object['info']

    card_title = object_name + " Information"
    reprompt_text = "You can ask me about other celestial objects or planets by saying, tell me about earth."
                    
    should_end_session = False

    send_message(str(stellar_object['index']))

    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Display Intents (Unity Bridge)----------------------

def display_planet( intent, session ):
   
    reprompt_text = "You can ask me about other celestial objects or planets by saying, tell me about earth."             
    should_end_session = False
    planet = get_response(intent, session,'celestial')['Item']
    planet_name = planet['name']
    card_title = "Display " + planet_name
    index = str(planet['index'])
    send_message(index)
    speech_output = "Displaying " + planet_name
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def restore_unity(object,session):
    table = dynamodb.Table('celestials')
    response = table.get_item(
        Key={
            'name': object
        }
    )
    response = response['Item']
    index = str(response['index'])
    send_message(index)
    return


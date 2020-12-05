from flask import Flask, Response, request
from cgi import parse_multipart, parse_header
from io import BytesIO
from base64 import b64decode

# Lidar com arquivos JSON
import json, os

# Lidar com arquivos
from os.path import join, dirname

# Aqui importamos as classes que cuidam dos serviços do Natural Language Understanding e do Speech-to-Text
from ibm_watson import NaturalLanguageUnderstandingV1, SpeechToTextV1

# Puxamos, para o natural language understanding, as classes de Features e EntitiesOptions que serão úteis para obter as entidades e os sentimentos associdados
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions

# Só é possível se conectar aos seus serviços se você se autenticar, e a classe que cuidará disso é o IAMAuthenticator
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

app = Flask(__name__)

@app.route("/", methods=["POST","GET"])
def main(args):

    # Parse incoming request headers
    _c_type, p_dict = parse_header(
        args['__ow_headers']['content-type']
    )
    
    # Decode body (base64)
    decoded_string = b64decode(args['__ow_body'])

    # Set Headers for multipart_data parsing
    p_dict['boundary'] = bytes(p_dict['boundary'], "utf-8")
    p_dict['CONTENT-LENGTH'] = len(decoded_string)
    
    # Parse incoming request data
    multipart_data = parse_multipart(
        BytesIO(decoded_string), p_dict
    )    

    # Build flac file from stream of bytes
    fo = open("audio_sample.flac", 'wb')
    fo.write(multipart_data.get('audio')[0])
    fo.close()

    car = multipart_data.get('car')[0]
    text = multipart_data.get('text')[0]

    """## Serviço NLU

    Você precisará de 3 coisas: A key e a URL do seu serviço de `Natural Language Understanding` e o model_id do seu Knowledge Studio treinado.
    """

    nlu_apikey = "R5Kq3Z4sJbPaepfWCC1d3iYch2kIEHJkF1sqnHZTC-C3"
        
    nlu_service_url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/d26c8f6f-666f-44eb-a631-cb8b161f0c48"
        
    nlu_entity_model = "a52546bf-6061-4fd0-a3ec-f2e6aa6d19b9"

    """Agora instanciamos os serviços com as suas credenciais."""

    # Cria-se um autenticador
    nlu_authenticator = IAMAuthenticator(apikey=nlu_apikey)

    # Criamos o serviço passando esse autenticador
    nlu_service = NaturalLanguageUnderstandingV1(
        version='2018-03-16',
        authenticator=nlu_authenticator)

    # Setamos a URL de acesso do nosso serviço
    nlu_service.set_service_url(nlu_service_url)

    ## Serviço STT

    stt_apikey = "-pCzIHgC12ljTpVXELSfx71BAP2yUmAlacQaD1YXdZqM"

    stt_service_url = "https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/2dda5ef8-4933-4096-8fb6-ad817e0e105c"

    """E agora instanciamos o serviço com as suas credenciais."""

    stt_authenticator = IAMAuthenticator(apikey=stt_apikey)

    stt_service = SpeechToTextV1(authenticator=stt_authenticator)

    stt_service.set_service_url(stt_service_url)

    stt_model = 'pt-BR_BroadbandModel'

    if audio:    

        # Read audio file and call Watson STT API:
        with open(
            os.path.join(
                os.path.dirname(__file__), './.',
                'audio_sample.flac'
            ), 'rb'
        ) as audio_file:
            # Transcribe the audio.flac with Watson STT
            # Recognize method API reference: 
            # https://cloud.ibm.com/apidocs/speech-to-text?code=python#recognize
            stt_result = stt.recognize(
                audio=audio_file,
                content_type='audio/flac',
                model='pt-BR_BroadbandModel'
            ).get_result()

        results_stt = json.loads(json.dumps(stt_results, indent=2, ensure_ascii=False))

        text = results_stt['results'][0]['alternatives'][0]['transcript']

        # Return a dictionary with the transcribed text
        #return {
        #    "transcript": stt_result['results'][0]['alternatives'][0]['transcript']
        #}

    # O método analyze cuida de tudo
    nlu_response = nlu_service.analyze(
        text=text,
        features=Features(entities=EntitiesOptions(model=nlu_entity_model, sentiment=True)),
        language='pt'
    ).get_result()

    results_nlu = json.loads((json.dumps(nlu_response, indent=2, ensure_ascii=False)))

    return results_nlu
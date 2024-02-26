from zeep import Client
from dotenv import load_dotenv
import os

load_dotenv()

ID_CONSULTANTE = os.environ['ID_CONSULTANTE']
SENHA_CONSULTANTE = os.environ['SENHA_CONSULTANTE']

def consultar_processo(id_consultante, senha_consultante, numero_processo, grau=1):
    wsdl = f'https://pje.tjpi.jus.br/{grau}g/intercomunicacao?wsdl'
    client = Client(wsdl=wsdl)

    with client.settings(raw_response=True, strict=False):
        response = client.service.consultarProcesso(
            id_consultante, senha_consultante, numero_processo
        )
        content = response.content
    return content


numero_processo = '1234'
print(consultar_processo(ID_CONSULTANTE, SENHA_CONSULTANTE, numero_processo))
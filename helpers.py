from lxml import etree
from zeep import Client
from requests.exceptions import RequestException

def extrair_xml(response_data):
    start_index = response_data.find('<soap:Envelope')
    stop = '</soap:Envelope>'
    stop_index = response_data.find(stop) + len(stop)
    xml = response_data[start_index:stop_index]
    return xml


def validar_xml(xml):
    tree = etree.fromstring(xml)
    schema = etree.XMLSchema(file='schema.xsd')
    return schema.validate(tree)


def consultar_processo(id_consultante, senha_consultante, numero_processo, grau=1):
    wsdl = f'https://pje.tjpi.jus.br/{grau}g/intercomunicacao?wsdl'
    client = Client(wsdl=wsdl)

    with client.settings(raw_response=True, strict=False):
        try:
            response = client.service.consultarProcesso(
                id_consultante, senha_consultante, numero_processo
            )
            content = extrair_xml(str(response.content))
        except RequestException as e:
            print(f'Erro de conexão: {e}')

    if not validar_xml(content):
        return False
    
    return content

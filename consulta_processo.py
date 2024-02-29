from lxml import etree
import xml.etree.ElementTree as ET
from zeep import Client
from requests.exceptions import RequestException

class ConsultaProcesso:
    def __init__(self, id_consultante, senha_consultante, numero_processo, grau=1):
        self.id_consultante = id_consultante
        self.senha_consultante = senha_consultante
        self.numero_processo = numero_processo
        self.grau = grau


    def __extrair_xml(self, response_data, start, stop):
        start_index = response_data.find(start)
        stop_index = response_data.find(stop) + len(stop)
        xml = response_data[start_index:stop_index]
        return xml


    def __validar_xml(self, xml):
        tree = etree.fromstring(xml)
        schema = etree.XMLSchema(file='schema.xsd')
        return schema.validate(tree)
    

    def __xml_para_dict(self, element):
        dict_element = element.attrib.copy()
        if element.text:
            dict_element['_text'] = element.text
        for child in element:
            key = child.tag.split('}')[1]
            if key in dict_element:
                if not isinstance(dict_element[key], list):
                    dict_element[key] = [dict_element[key]]
                dict_element[key].append(self.__xml_para_dict(child))
            else:
                dict_element[key] = self.__xml_para_dict(child)
        return dict_element

    def consultar_processo(self):
        wsdl = f'https://pje.tjpi.jus.br/{self.grau}g/intercomunicacao?wsdl'
        client = Client(wsdl=wsdl)
        with client.settings(raw_response=True, strict=False):
            try:
                response = client.service.consultarProcesso(
                    self.id_consultante, self.senha_consultante, self.numero_processo,
                    incluirCabecalho=True, movimentos=True, incluirDocumentos=True
                )
                content = self.__extrair_xml(str(response.text), start='<soap:Envelope', stop='</soap:Envelope>')
            except RequestException as e:
                print(f'Erro de conexão: {e}')
                return False
        if not self.__validar_xml(content):
            print('XML inválido.')
            return False
        return content


    def dados_basicos(self):
        dados_processo = self.consultar_processo()
        root = ET.fromstring(dados_processo)
        return self.__xml_para_dict(root)['Body']['consultarProcessoResposta']['processo']['dadosBasicos']


    def movimentos(self):
        dados_processo = self.consultar_processo()
        root = ET.fromstring(dados_processo)
        return self.__xml_para_dict(root)['Body']['consultarProcessoResposta']['processo']['movimento']


    def documentos(self):
        dados_processo = self.consultar_processo()
        root = ET.fromstring(dados_processo)
        return self.__xml_para_dict(root)['Body']['consultarProcessoResposta']['processo']['documento']

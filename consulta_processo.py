from lxml import etree
import xml.etree.ElementTree as ET
from zeep import Client, Settings
from requests.exceptions import RequestException
import base64
import mimetypes
from more_itertools import chunked

class PjeProcess:
    def __init__(self, id_consultante, senha_consultante, numero_processo, grau=1):
        self.id_consultante = id_consultante
        self.senha_consultante = senha_consultante
        self.numero_processo = numero_processo
        self.grau = grau


    def extract_xml(self, response_data, start, stop):
        start_index = response_data.find(start)
        stop_index = response_data.find(stop) + len(stop)
        xml = response_data[start_index:stop_index]
        return xml
    

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
                content = self.extract_xml(str(response.text), start='<soap:Envelope', stop='</soap:Envelope>')
            except RequestException as e:
                print(f'Erro de conexão: {e}')
                return False
        return content


    def dados_basicos(self):
        dados_processo = self.consultar_processo()
        root = ET.fromstring(dados_processo)
        try:
            return self.__xml_para_dict(root)['Body']['consultarProcessoResposta']['processo']['dadosBasicos']
        except KeyError:
            return False


    def get_attributes_from_movement(self, movement_element):
        complement = movement_element.find('.//ns2:complemento', namespaces={'ns2': 'http://www.cnj.jus.br/intercomunicacao-2.2.2'})
        linked_document_id = movement_element.find('.//ns2:idDocumentoVinculado', namespaces={'ns2': 'http://www.cnj.jus.br/intercomunicacao-2.2.2'})
        return {
            'process_number': self.numero_processo,
            'datetime': movement_element.attrib['dataHora'],
            'identifier': movement_element.attrib['identificadorMovimento'],
            'complement': complement.text,
            'linked_document_id': linked_document_id.text if linked_document_id is not None else None
        }
    

    def get_attributes_from_document(self, document_element):
        return {
            'identifier': document_element.attrib.get('idDocumento', ''),
            'movement': document_element.attrib.get('movimento', ''),
            'datetime': document_element.attrib.get('dataHora', ''),
            'mime_type': document_element.attrib.get('mimetype', ''),
            'description': document_element.attrib.get('descricao', ''),
            'linked_documents': [],
        }


    def get_movements(self):
        dados_processo = self.consultar_processo()
        tree = etree.fromstring(dados_processo)
        find = etree.XPath('//ns2:movimento', namespaces={'ns2': 'http://www.cnj.jus.br/intercomunicacao-2.2.2'})
        movements = find(tree)
        movements = list(map(self.get_attributes_from_movement, movements))
        return movements


    def get_movement_by_id(self, id):
        process_data = self.consultar_processo()
        tree = etree.fromstring(process_data)
        find = etree.XPath(f'//ns2:movimento[@identificadorMovimento={id}]', namespaces={'ns2': 'http://www.cnj.jus.br/intercomunicacao-2.2.2'})
        movement = find(tree)

        if not movement:
            return movement
        
        return [self.get_attributes_from_movement(movement[0])]


    def get_document_by_id(self, id):
        process_data = self.consultar_processo()
        tree = etree.fromstring(process_data)
        document = tree.xpath(f'//ns2:documento[@idDocumento={id}]', namespaces={'ns2': 'http://www.cnj.jus.br/intercomunicacao-2.2.2'})
        linked_documents = document[0].findall('.//ns2:documentoVinculado', namespaces={'ns2': 'http://www.cnj.jus.br/intercomunicacao-2.2.2'})
        document_attributes = self.get_attributes_from_document(document[0])
        if linked_documents:
            for linked_document in linked_documents:
                document_attributes['linked_documents'].append(self.get_attributes_from_document(linked_document))
        return document_attributes
    

    def download_document(self, document):
        wsdl = f'https://pje.tjpi.jus.br/{self.grau}g/intercomunicacao?wsdl'
        setttings = Settings(raw_response=False, strict=False)
        client = Client(wsdl=wsdl, settings=setttings)
        try:
            document_ids = [document.get('identifier')]
            linked_documents = document['linked_documents']
            if linked_documents:
                for linked_document in linked_documents:
                    document_ids.append(linked_document.get('identifier'))

            response = client.service.consultarProcesso(
                self.id_consultante, self.senha_consultante, self.numero_processo,
                incluirCabecalho=False, movimentos=False, incluirDocumentos=False, documento=document_ids
            )

            doc = response.processo.documento[0]

            extension = mimetypes.guess_extension(doc['mimetype'])
            mimetype = extension if extension is not None else f'.{doc["mimetype"]}'
            with open('files/'+doc['hash']+doc['descricao']+mimetype, 'wb') as file_document:
                file_document.write(doc['conteudo'])

            documento_vinculado = doc['_value_1']
            if documento_vinculado is not None:
                conteudo_documento_vinculado = documento_vinculado.find('{http://www.cnj.jus.br/intercomunicacao-2.2.2}conteudo')
                data = base64.b64decode(conteudo_documento_vinculado.text)
                extension = mimetypes.guess_extension(documento_vinculado.attrib['mimetype'])
                mimetype = extension if extension is not None else f'.{documento_vinculado.attrib["mimetype"]}'
                with open('files/'+documento_vinculado.attrib['hash']+documento_vinculado.attrib['descricao']+mimetype, 'wb') as file_document:
                    file_document.write(data)
        
            if doc['documentoVinculado']:
                for d in doc['documentoVinculado']:
                    extension = mimetypes.guess_extension(d['mimetype'])
                    mimetype = extension if extension is not None else f'.{d["mimetype"]}'
                    with open('files/'+d['hash']+d['descricao']+mimetype, 'wb') as file_document:
                        file_document.write(d['conteudo'])
        except RequestException as e:
            print(f'Erro de conexão: {e}')
            return False

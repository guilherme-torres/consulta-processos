from lxml import etree
import xml.etree.ElementTree as ET
from zeep import Client, Settings
from requests.exceptions import RequestException
import base64
import mimetypes
from more_itertools import chunked

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
        dados_processo = self.__consultar_processo()
        root = ET.fromstring(dados_processo)
        try:
            return self.__xml_para_dict(root)['Body']['consultarProcessoResposta']['processo']['dadosBasicos']
        except KeyError:
            return False


    def movimentos(self):
        dados_processo = self.__consultar_processo()
        root = ET.fromstring(dados_processo)
        try:
            return self.__xml_para_dict(root)['Body']['consultarProcessoResposta']['processo']['movimento']
        except KeyError:
            return False


    def get_documents_id(self):
        process_data = self.consultar_processo()
        tree = etree.fromstring(process_data)
        documents_id = []
        documents = tree.xpath('//*[@idDocumento]')
        for document in documents:
            document_id = document.get('idDocumento')
            documents_id.append(document_id)
        return documents_id
    

    def download_attachments(self, document_ids, chunk_size=10):
        wsdl = f'https://pje.tjpi.jus.br/{self.grau}g/intercomunicacao?wsdl'
        setttings = Settings(raw_response=False, strict=False)
        client = Client(wsdl=wsdl, settings=setttings)
        for chunk in chunked(document_ids, chunk_size):
            try:
                response = client.service.consultarProcesso(
                    self.id_consultante, self.senha_consultante, self.numero_processo,
                    incluirCabecalho=False, movimentos=False, incluirDocumentos=False, documento=chunk
                )
                for doc in response.processo.documento:
                    # print({
                    #     'identifier': doc['idDocumento'],
                    #     'datetime': doc['dataHora'],
                    #     'mime_type': doc['mimetype'],
                    #     'description': doc['descricao'],
                    # })
                    extension = mimetypes.guess_extension(doc['mimetype'])
                    mimetype = extension if extension is not None else f'.{doc["mimetype"]}'
                    with open('files/'+doc['hash']+doc['descricao']+mimetype, 'wb') as file_document:
                        file_document.write(doc['conteudo'])
                    # print(doc['idDocumento'])

                    # primeiro documento vinculado
                    documento_vinculado = doc['_value_1']
                    if documento_vinculado is not None:
                        # print(documento_vinculado.attrib['idDocumento'])
                        conteudo_documento_vinculado = documento_vinculado.find('{http://www.cnj.jus.br/intercomunicacao-2.2.2}conteudo')
                        data = base64.b64decode(conteudo_documento_vinculado.text)
                        extension = mimetypes.guess_extension(documento_vinculado.attrib['mimetype'])
                        mimetype = extension if extension is not None else f'.{documento_vinculado.attrib["mimetype"]}'
                        with open('files/'+documento_vinculado.attrib['hash']+documento_vinculado.attrib['descricao']+mimetype, 'wb') as file_document:
                            file_document.write(data)
                    
                    # outros documentos vinculados
                    if doc['documentoVinculado']:
                        for d in doc['documentoVinculado']:
                            # print(d['idDocumento'])
                            extension = mimetypes.guess_extension(d['mimetype'])
                            mimetype = extension if extension is not None else f'.{d["mimetype"]}'
                            with open('files/'+d['hash']+d['descricao']+mimetype, 'wb') as file_document:
                                file_document.write(d['conteudo'])
                    
                        
            except RequestException as e:
                print(f'Erro de conexão: {e}')
                return False

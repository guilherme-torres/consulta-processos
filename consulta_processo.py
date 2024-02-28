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
        raiz = ET.fromstring(dados_processo)
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns': 'http://www.cnj.jus.br/tipos-servico-intercomunicacao-2.2.2',
            'ns2': 'http://www.cnj.jus.br/intercomunicacao-2.2.2',
            'ns3': 'http://www.cnj.jus.br/mni/cda',
            'ns4': 'http://www.cnj.jus.br/servico-intercomunicacao-2.2.2/'
        }
        dados_basicos_element = raiz[0][0][2].find('ns2:dadosBasicos', namespaces)
        dados_basicos = dict()
        for dados in dados_basicos_element:
            # Polo
            if dados.tag == '{http://www.cnj.jus.br/intercomunicacao-2.2.2}polo':
                if dados.attrib['polo'] in ('AT', 'PA'):
                    polo = dados_basicos_element.find(f'ns2:polo[@polo="{dados.attrib['polo']}"]', namespaces)

                    parte = polo.find('ns2:parte', namespaces)

                    # Dados da pessoa
                    pessoa = parte.find('ns2:pessoa', namespaces)
                    documento = pessoa.find('ns2:documento', namespaces)
                    endereco = pessoa.find('ns2:endereco', namespaces)
                    logradouro = endereco.find('ns2:logradouro', namespaces)
                    numero = endereco.find('ns2:numero', namespaces)
                    complemento = endereco.find('ns2:complemento', namespaces)
                    bairro = endereco.find('ns2:bairro', namespaces)
                    cidade = endereco.find('ns2:cidade', namespaces)
                    estado = endereco.find('ns2:estado', namespaces)

                    # Dados do advogado
                    advogados = parte.findall('ns2:advogado', namespaces)

                    dados_polo = dict()
                    dados_polo['parte'] = parte.tag
                    dados_basicos[f'polo{dados.attrib['polo']}'] = dados_polo

                    dados_pessoa = dict()
                    dados_documento = documento.attrib
                    # codigoDocumento emissorDocumento tipoDocumento nome
                    dados_pessoa['documento'] = dados_documento
                    dados_pessoa['nome'] = pessoa.attrib['nome']
                    dados_pessoa['cep'] = endereco.attrib['cep']
                    dados_pessoa['logradouro'] = logradouro.text
                    dados_pessoa['numero'] = numero.text
                    if complemento is not None:
                        dados_pessoa['complemento'] = complemento.text
                    dados_pessoa['bairro'] = bairro.text
                    dados_pessoa['cidade'] = cidade.text
                    dados_pessoa['estado'] = estado.text
                    dados_polo['pessoa'] = dados_pessoa

                    # dados_polo['advogados'] = dict()
                    # for advogado in advogados:
                    #     dados_polo['advogados'] = advogado.tag
            # Assunto
            if dados.tag == '{http://www.cnj.jus.br/intercomunicacao-2.2.2}assunto':
                assunto = dados_basicos_element.find('ns2:assunto', namespaces)
                codigo_nacional = assunto.find('ns2:codigoNacional', namespaces)

                dados_basicos['assunto'] = assunto.tag
                dados_basicos['codigoNacional'] = codigo_nacional.text
            # Magistrado atuante
            if dados.tag == '{http://www.cnj.jus.br/intercomunicacao-2.2.2}magistradoAtuante':
                magistrado_atuante = dados_basicos_element.find('ns2:magistradoAtuante', namespaces)
                dados_basicos['magistradoAtuante'] = magistrado_atuante.text
            # Valor causa
            if dados.tag == '{http://www.cnj.jus.br/intercomunicacao-2.2.2}valorCausa':
                valor_causa = dados_basicos_element.find('ns2:valorCausa', namespaces)
                dados_basicos['valorCausa'] = valor_causa.text
            # Orgao julgador
            if dados.tag == '{http://www.cnj.jus.br/intercomunicacao-2.2.2}orgaoJulgador':
                orgao_julgador = dados_basicos_element.find('ns2:orgaoJulgador', namespaces)
                dados_orgao_julgador = dict()
                dados_orgao_julgador['codigoOrgao'] = orgao_julgador.attrib['codigoOrgao']
                dados_orgao_julgador['nomeOrgao'] = orgao_julgador.attrib['codigoOrgao']
                dados_orgao_julgador['instancia'] = orgao_julgador.attrib['instancia']
                dados_orgao_julgador['codigoMunicipioIBGE'] = orgao_julgador.attrib['codigoMunicipioIBGE']
                dados_basicos['orgao_julgador'] = dados_orgao_julgador
        return dados_basicos


    def movimentos(self):
        dados_processo = self.consultar_processo()
        tree = etree.fromstring(dados_processo)
        return tree


    def documentos(self):
        dados_processo = self.consultar_processo()
        tree = etree.fromstring(dados_processo)
        return tree

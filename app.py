from dotenv import load_dotenv
import os
from consulta_processo import ConsultaProcesso

load_dotenv()

ID_CONSULTANTE = os.environ['ID_CONSULTANTE']
SENHA_CONSULTANTE = os.environ['SENHA_CONSULTANTE']

numero_processo = ''
documentos_id = ConsultaProcesso(ID_CONSULTANTE, SENHA_CONSULTANTE, numero_processo).get_documents_id()
ConsultaProcesso(ID_CONSULTANTE, SENHA_CONSULTANTE, numero_processo).download_attachments(documentos_id)
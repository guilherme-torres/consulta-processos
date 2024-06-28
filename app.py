from dotenv import load_dotenv
import os
from consulta_processo import PjeProcess

load_dotenv()

PJE_ID = os.environ['ID_CONSULTANTE']
PJE_PASSWORD = os.environ['SENHA_CONSULTANTE']

process_number = ''
process = PjeProcess(PJE_ID, PJE_PASSWORD, process_number)

movement = process.get_movement_by_id('75514781')
document = process.get_document_by_id(movement[0].get('linked_document_id'))
process.download_document(document)
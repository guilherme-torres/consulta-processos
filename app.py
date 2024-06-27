from dotenv import load_dotenv
import os
from consulta_processo import PjeProcess

load_dotenv()

PJE_ID = os.environ['ID_CONSULTANTE']
PJE_PASSWORD = os.environ['SENHA_CONSULTANTE']

process_number = '0816547-72.2023.8.18.0140'
process = PjeProcess(PJE_ID, PJE_PASSWORD, process_number)
movements = process.get_movement_by_id('75745205')
document_ids = process.get_documents_attached_to_movements(movements)
# print(movements)
print(document_ids)
# print(document_ids)
# process.download_documents(document_ids)
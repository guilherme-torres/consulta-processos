from dotenv import load_dotenv
import os
from helpers import consultar_processo

load_dotenv()

ID_CONSULTANTE = os.environ['ID_CONSULTANTE']
SENHA_CONSULTANTE = os.environ['SENHA_CONSULTANTE']

numero_processo = '1234'
print(consultar_processo(ID_CONSULTANTE, SENHA_CONSULTANTE, numero_processo))
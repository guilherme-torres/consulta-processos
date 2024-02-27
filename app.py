from dotenv import load_dotenv
import os
from consulta_processo import ConsultaProcesso

load_dotenv()

ID_CONSULTANTE = os.environ['ID_CONSULTANTE']
SENHA_CONSULTANTE = os.environ['SENHA_CONSULTANTE']

numero_processo = '0816547-72.2023.8.18.0140'
ConsultaProcesso(ID_CONSULTANTE, SENHA_CONSULTANTE, numero_processo).dados_basicos()
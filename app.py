from dotenv import load_dotenv
import os
from consulta_processo import ConsultaProcesso

load_dotenv()

ID_CONSULTANTE = os.environ['ID_CONSULTANTE']
SENHA_CONSULTANTE = os.environ['SENHA_CONSULTANTE']

numero_processo = '1234'
dados_processo = ConsultaProcesso(ID_CONSULTANTE, SENHA_CONSULTANTE, numero_processo).dados_basicos()
print(dados_processo)
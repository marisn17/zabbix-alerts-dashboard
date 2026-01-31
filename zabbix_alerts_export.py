import requests
from datetime import datetime, timedelta
import pandas as pd
 
# Configurações da API
url = 'http://10.2.5.10/api_jsonrpc.php'
token = "04fda8420301cc28e4c47feb0360a5b10a07de43946e17d25d0b7cbea42f429f"
headers = {'Content-Type': 'application/json-rpc'}
 
# Intervalo de tempo
now = datetime.now()
# time_from = int((now - timedelta(days=15)).timestamp())
# time_till = int(now.timestamp())
 
time_from = '1738368000'
time_till = '1740518399'
 
def zabbix_request(payload):
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['result']
 
# 1. Buscar eventos de problema
event_payload = {
    "jsonrpc": "2.0",
    "method": "event.get",
    "params": {
        "output": ["eventid", "clock", "name", "objectid","severity"],
        "selectHosts": ["hostid", "host"],
        # "groupids": [],
        "source": 0,
        "object": 0,
        "value": 1,
        "time_from": time_from,
        "time_till": time_till,
        "sortfield": "clock",
        "sortorder": "DESC",
        "limit": 5000
    },
    "auth": token,
    "id": 1
}
 
events = zabbix_request(event_payload)
 
# 2. Obter triggerid únicos
trigger_ids = list({e['objectid'] for e in events})
 
# 3. Buscar descrição da trigger e tags
trigger_payload = {
    "jsonrpc": "2.0",
    "method": "trigger.get",
    "params": {
        "triggerids": trigger_ids,
        "output": ["triggerid", "description"],
       
    },
    "auth": token,
    "id": 2
}
 
triggers = zabbix_request(trigger_payload)
 
# Mapear triggerid -> descrição e tags
trigger_info = {
    t['triggerid']: {
        'description': t['description'],
        'tags': t.get('tags', [])
    } for t in triggers
}
severity_map = {
    "0": "Não classificado",
    "1": "Informação",
    "2": "Aviso",
    "3": "Médio",
    "4": "Alto",
    "5": "Desastre"
}
 
# 4. Criar lista detalhada por evento
result_data = []
 
for e in events:
    triggerid = e['objectid']
    tinfo = trigger_info.get(triggerid)
    if not tinfo:
        continue
 
    description = tinfo['description']
    tag_string = ", ".join([f"{t['tag']}={t['value']}" for t in tinfo['tags']]) or "Sem Tag"
    clock = datetime.fromtimestamp(int(e['clock'])).strftime('%Y-%m-%d %H:%M:%S')
 
# Pega severidade do evento
    severity = severity_map.get(str(e['severity']), "Desconhecida")
   
    for host in e.get('hosts', []):
        result_data.append({
            "Host": host['host'],
            "Data/Hora": clock,
            "Descrição do Alerta": description,
            "Severidade": severity,
        })
 
# 5. Gerar DataFrame e salvar
df = pd.DataFrame(result_data)
 
data_atual = now.strftime("%Y-%m-%d_%H-%M")
csv_file = f"lista_alertas_{data_atual}.csv"
excel_file = f"lista_alertas_{data_atual}.xlsx"
 
df.to_csv(csv_file, index=False, encoding='utf-8-sig')
df.to_excel(excel_file, index=False)
 
print(f"\n✅ Arquivos gerados com sucesso:")
print(f"→ {csv_file}")
print(f"→ {excel_file}")
 
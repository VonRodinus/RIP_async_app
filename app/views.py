from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor

CALLBACK_URL = "http://localhost:8080/api/tpq_requests/"
GO_API_URL   = "http://localhost:8080/api/tpq_requests/"
TOKEN        = "A1B2C3D4"
GO_TOKEN     = ""    

executor = ThreadPoolExecutor(max_workers=1)

def calculate_tpq_async(pk: str):
    time.sleep(random.randint(6, 11))

    headers = {}
    if GO_TOKEN:
        headers["Authorization"] = f"Bearer {GO_TOKEN}"

    try:
        resp = requests.get(f"{GO_API_URL}{pk}", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"Заявка получена: {len(data.get('items', []))} позиций")
    except Exception as e:
        print("Ошибка получения заявки:", e)
        return None

    items = data.get("items", [])
    if not items:
        print("В заявке нет артефактов → TPQ = 0")
        return {"id": pk, "result_tpq": 0}

    tpq_values = []
    for item in items:
        artifact = item.get("Artifact")
        if artifact and "tpq" in artifact:
            tpq_values.append(artifact["tpq"])

    max_tpq = max(tpq_values) if tpq_values else 0
    print(f"TPQ артефактов: {tpq_values} → максимум = {max_tpq}")

    return {"id": pk, "result_tpq": max_tpq}


def send_result(task):
    result = task.result()
    if not result:
        return

    url = f"{CALLBACK_URL}{result['id']}/moderate"
    payload = {
        "result_tpq": result["result_tpq"],
        "token": TOKEN
    }

    try:
        r = requests.put(url, json=payload, timeout=10)
        print(f"TPQ рассчитан и отправлен: {result['result_tpq']} → HTTP {r.status_code}")
    except Exception as e:
        print("Ошибка отправки результата:", e)


@api_view(['POST'])
def moderate_request(request):
    if "pk" not in request.data:
        return Response({"error": "pk required"}, status=400)

    pk = request.data["pk"]
    task = executor.submit(calculate_tpq_async, pk)
    task.add_done_callback(send_result)

    return Response({"message": "tpq calculation started", "id": pk}, status=200)
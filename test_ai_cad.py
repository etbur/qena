import os, sys, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from django.test import RequestFactory
from makerspace.views import api_ai_cad_generate

rf = RequestFactory()
prompt_text = "Generate a heavy-duty robotic arm bracket with 4 M6 mounting holes"
req = rf.post('/makerspace/api/ai-cad-generate/', data=json.dumps({'prompt': prompt_text}), content_type='application/json')
res = api_ai_cad_generate(req)
print("POST Response status:", res.status_code)
print("POST Response content:", res.content.decode('utf-8'))

req_get = rf.get('/makerspace/api/ai-cad-generate/?prompt=' + prompt_text)
res_get = api_ai_cad_generate(req_get)
print("GET Response status:", res_get.status_code)
print("GET Response content:", res_get.content.decode('utf-8'))

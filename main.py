from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import face_recognition
import shutil
import os
import requests

app = FastAPI()

# Configura CORS (ainda que não esteja sendo necessário, mantemos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota para verificação facial
@app.post("/verificar")
async def verificar(imagem: UploadFile = File(...)):
    with open("recebida.jpg", "wb") as f:
        shutil.copyfileobj(imagem.file, f)

    img = face_recognition.load_image_file("recebida.jpg")
    encoding = face_recognition.face_encodings(img)

    if not encoding:
        return {"autorizado": False, "msg": "Nenhum rosto encontrado"}

    for nome_arquivo in os.listdir("rostos"):
        ref = face_recognition.load_image_file(f"rostos/{nome_arquivo}")
        enc_ref = face_recognition.face_encodings(ref)
        if enc_ref and face_recognition.compare_faces(enc_ref, encoding[0])[0]:
            pessoa = os.path.splitext(nome_arquivo)[0]

            # Envia PUT para o Back4App
            back4app_url = "https://parseapi.back4app.com/classes/esp32/aczejEuhPn"
            headers = {
                "X-Parse-Application-Id": "4RkqUjQ5dyL7k0RbQyGz2ArZMjoIPz9Qb3VuGUKU",
                "X-Parse-REST-API-Key": "WkO0917Kzrx3oqWV4QDVDgbeTAuKI1crrbxAwvaE",
                "Content-Type": "application/json"
            }
            payload = { "ligado": True }
            try:
                r = requests.put(back4app_url, json=payload, headers=headers)
                status = r.status_code
            except Exception as e:
                status = f"Erro ao enviar para Back4App: {e}"

            return {
                "autorizado": True,
                "pessoa": pessoa,
                "back4app": status
            }

    return {"autorizado": False}

# Rota para cadastrar novo rosto
@app.post("/cadastrar")
async def cadastrar(nome: str = Form(...), imagem: UploadFile = File(...)):
    os.makedirs("rostos", exist_ok=True)
    caminho = os.path.join("rostos", f"{nome}.jpg")
    with open(caminho, "wb") as f:
        shutil.copyfileobj(imagem.file, f)
    return {"status": "ok", "msg": f"Rosto de {nome} cadastrado com sucesso."}

# Servir HTML da pasta /site
app.mount("/", StaticFiles(directory="site", html=True), name="site")

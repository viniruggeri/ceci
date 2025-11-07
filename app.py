# app.py
import json
import os
import tempfile
import uuid
from typing import Optional

import jwt
from jwt import InvalidTokenError
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from pipeline import process_user_input  # seu generator async

# Config
SECRET = "minhaChaveSuperSecretaParaJwtComTamanhoAdequado!"  # substitua por env var em produção
HISTORICO_FILE = "historico.json"

app = FastAPI(
    title="Ceci - São Paulo Transport Assistant API",
    description="API para assistente de transporte público de São Paulo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Health Check ----------
@app.get("/")
def root():
    """Endpoint raiz - informações da API"""
    return {
        "service": "Ceci Transport Assistant",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "chat": "/ceci/chat (WebSocket)",
            "historico": "/ceci/historico",
            "reports": "/reports/download/{filename}"
        }
    }


@app.get("/health")
def health_check():
    """Health check para Azure monitoring"""
    return {
        "status": "healthy",
        "service": "ceci-api",
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


# ---------- utils de arquivo (seguro contra JSON vazio/corrompido) ----------
def get_login_from_token(token: str) -> Optional[str]:
    """
    Retorna o login do usuário (sub) a partir do token JWT.
    """
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET, algorithms=["HS256"])
        return payload.get("login")  # login do usuário (era "sub", mas usamos "login")
    except InvalidTokenError:
        return None

    
def garantir_arquivo_inicial():
    """Garante que o arquivo exista e seja um dict JSON válido."""
    if not os.path.exists(HISTORICO_FILE) or os.path.getsize(HISTORICO_FILE) == 0:
        with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
            f.write("{}")
        return

    # tenta validar conteúdo; se inválido, reseta para {}
    try:
        with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if not conteudo:
                with open(HISTORICO_FILE, "w", encoding="utf-8") as fw:
                    fw.write("{}")
                return
            dados = json.loads(conteudo)
            if not isinstance(dados, dict):
                with open(HISTORICO_FILE, "w", encoding="utf-8") as fw:
                    fw.write("{}")
    except (json.JSONDecodeError, OSError):
        with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
            f.write("{}")


def carregar_historico_json():
    garantir_arquivo_inicial()
    try:
        with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if not isinstance(dados, dict):
                return {}
            return dados
    except (json.JSONDecodeError, OSError):
        # reset por segurança
        with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
            f.write("{}")
        return {}


def escrever_json_atomico(dados):
    """Escreve o JSON de forma atômica: temp file -> replace"""
    dir_name = os.path.dirname(os.path.abspath(HISTORICO_FILE)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
            json.dump(dados, tmpf, ensure_ascii=False, indent=2)
            tmpf.flush()
            os.fsync(tmpf.fileno())
        os.replace(tmp_path, HISTORICO_FILE)
    except Exception:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


# ---------- histórico por token em blocos (colaborador <-> Ceci) ----------
def salvar_historico_bloco(token: str, colaborador_msg: Optional[str] = None, ceci_msg: Optional[str] = None):
    """
    Se colaborador_msg fornecido -> cria novo bloco {"mensagem_colaborador": ..., "mensagem_ceci": ...}
    Se apenas ceci_msg fornecido -> atualiza o último bloco para adicionar mensagem_ceci.
    """
    dados = carregar_historico_json()
    if token not in dados or not isinstance(dados[token], list):
        dados[token] = []

    if colaborador_msg is not None:
        # cria novo bloco (ceci_msg pode ser None)
        dados[token].append({
            "mensagem_colaborador": colaborador_msg,
            "mensagem_ceci": ceci_msg
        })
    elif ceci_msg is not None:
        # atualiza último bloco; se não existir, cria bloco com colaborador vazio
        if not dados[token]:
            dados[token].append({
                "mensagem_colaborador": "",
                "mensagem_ceci": ceci_msg
            })
        else:
            dados[token][-1]["mensagem_ceci"] = ceci_msg

    escrever_json_atomico(dados)


# ---------- endpoint para frontend buscar histórico ----------
@app.get("/ceci/historico")
def get_historico(authorization: Optional[str] = Header(None)):
    """
    Espera header Authorization: Bearer <token>
    Retorna lista de blocos do token (ou [] se não houver).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido")
    token = authorization.split(" ", 1)[1]
    login = get_login_from_token(token)
    if not login:
        raise HTTPException(status_code=401, detail="Token inválido")
    dados = carregar_historico_json()
    return dados.get(login, [])


# ---------- websocket endpoint ----------
@app.websocket("/ws/ceci")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    passenger_session_id: Optional[str] = None
    current_collaborator_login: Optional[str] = None
    try:
        while True:
            data = await websocket.receive_text()
            # payload esperado: { "usuario": "Colaborador"|"Passageiro", "texto": "<...>", "token": "<opt>" }
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text("Erro: payload inválido (JSON esperado).")
                continue

            tipoUsuario = msg.get("usuario", "Passageiro")
            texto = msg.get("texto", "")
            token = msg.get("token")
            session_id_to_use: Optional[str] = None

            # Se colaborador+token -> valida token e salva bloco de colaborador
            if tipoUsuario == "Colaborador" and token:
                login = get_login_from_token(token)
                if not login:
                    await websocket.send_text("Erro: token inválido.")
                    continue

                # salva a mensagem do colaborador (Ceci ainda não respondeu)
                salvar_historico_bloco(login, colaborador_msg=texto)
                current_collaborator_login = login
                session_id_to_use = f"collaborator::{login}"
            else:
                if passenger_session_id is None:
                    passenger_session_id = f"passageiro::{uuid.uuid4().hex}"
                session_id_to_use = passenger_session_id

            # Processa a mensagem com o pipeline (streaming)
            resposta_completa = ""
            try:
                async for chunk in process_user_input(
                    texto,
                    tipoUsuario,
                    token,
                    session_id=session_id_to_use,
                ):
                    await websocket.send_text(chunk)
                    resposta_completa += chunk
                await websocket.send_text("[DONE]")
            except Exception as e:
                # evita crash do servidor por erro na pipeline
                await websocket.send_text(f"Erro interno ao processar: {str(e)}")
                await websocket.send_text("[DONE]")
                continue

            # Se colaborador, atualiza o último bloco com a resposta da Ceci
            if tipoUsuario == "Colaborador" and current_collaborator_login:
                salvar_historico_bloco(current_collaborator_login, ceci_msg=resposta_completa)

    except WebSocketDisconnect:
        print("Client disconnected")


# ---------- Endpoints para PDFs ----------
@app.get("/reports/download/{filename}")
async def download_report(filename: str, authorization: str = Header(None)):
    """
    Endpoint para download de relatórios PDF.
    Apenas colaboradores autenticados podem baixar.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticação necessário")
    
    # Valida o token
    token = authorization.replace("Bearer ", "")
    login = get_login_from_token(token)
    if not login:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Verifica se o arquivo existe
    file_path = os.path.join("reports", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Retorna o arquivo
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/reports/list")
async def list_reports(authorization: str = Header(None)):
    """
    Lista todos os relatórios disponíveis para o colaborador autenticado.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticação necessário")
    
    # Valida o token e pega o nome do colaborador
    token = authorization.replace("Bearer ", "")
    login = get_login_from_token(token)
    if not login:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Lista arquivos PDF na pasta reports
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return {"reports": []}
    
    reports = []
    for filename in os.listdir(reports_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(reports_dir, filename)
            file_stats = os.stat(file_path)
            reports.append({
                "filename": filename,
                "size": file_stats.st_size,
                "created": file_stats.st_ctime,
                "download_url": f"/reports/download/{filename}"
            })
    
    return {"reports": reports}


# ---------- run (opcional) ----------
if __name__ == "__main__":
    import uvicorn
    print("Starting uvicorn on 0.0.0.0:5000")
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)
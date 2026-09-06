import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuração da API do Gemini via REST (leve e sem estourar memória do Render)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"

# Dados da Evolution API
EVOLUTION_URL = "https://evolution-api-production-5008.up.railway.app"
INSTANCE_NAME = "restaurante atendimento"
EVOLUTION_API_KEY = "55FDF751A44E-43F4-9768-1D0C01FE4979"

# Prompt do Sistema Focado em Delivery de Comida
SYSTEM_PROMPT = """
Você é um assistente virtual inteligente e simpático de um negócio de comida/delivery. 
Seu objetivo é atender os clientes no WhatsApp com muita cordialidade, agilidade e clareza.
Ajude os clientes informando sobre o cardápio, formas de pagamento, taxas de entrega, horários de funcionamento e tire dúvidas sobre os pratos.
Mantenha respostas diretas, amigáveis e com um toque acolhedor típico de atendimento de alimentação.
"""

@app.route("/", methods=["GET"])
def home():
    return "TestBot WhatsApp (Delivery) Rodando com Sucesso! 🚀", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("Dados recebidos da Evolution API:", data)
        
        # Filtra apenas eventos de mensagens novas
        if data.get("event") != "messages.upsert":
            return jsonify({"status": "ignored_event"}), 200

        raw_data = data.get("data", {})
        message_data = raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
        if not isinstance(message_data, dict):
            return jsonify({"status": "ignored"}), 200

        # Ignora se for mensagem enviada pelo próprio bot
        if message_data.get("key", {}).get("fromMe", False):
            return jsonify({"status": "ignored"}), 200

        # Extrai o conteúdo do texto
        msg_content = message_data.get("message", {})
        if not isinstance(msg_content, dict):
            return jsonify({"status": "ignored"}), 200

        message_body = msg_content.get("conversation") or msg_content.get("extendedTextMessage", {}).get("text", "")
        
        if not message_body:
            return jsonify({"status": "ignored_no_text"}), 200

        sender_number = message_data.get("key", {}).get("remoteJid", "")
        print(f"Mensagem de texto recebida de {sender_number}: {message_body}")

        # Monta a requisição para o Gemini via REST API (leve e sem erros de versão)
        gemini_payload = {
            "contents": [{"parts": [{"text": message_body}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]}
        }
        
        gemini_response = requests.post(GEMINI_URL, json=gemini_payload)
        gemini_data = gemini_response.json()
        
        # Extrai a resposta gerada
        try:
            reply_text = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            print("Erro ao extrair resposta do Gemini:", gemini_data)
            reply_text = "Olá! Recebi sua mensagem, mas tive um pequeno pico por aqui. Poderia repetir?"

        print(f"Resposta gerada pelo Gemini: {reply_text}")

        # Envia a resposta de volta para o cliente via Evolution API
        send_url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "number": sender_number.replace("@s.whatsapp.net", "").replace("@g.us", ""),
            "text": reply_text
        }
        
        requests.post(send_url, json=payload, headers=headers)

        return jsonify({"status": "success", "reply": reply_text}), 200

    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

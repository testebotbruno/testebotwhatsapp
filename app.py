import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Configuração do Gemini API usando a nova SDK oficial (google-genai)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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

        # Extrai o conteúdo do texto apenas se for uma mensagem de texto válida
        msg_content = message_data.get("message", {})
        if not isinstance(msg_content, dict):
            return jsonify({"status": "ignored"}), 200

        message_body = msg_content.get("conversation") or msg_content.get("extendedTextMessage", {}).get("text", "")
        
        # Se não houver texto puro (ex: foi emoji, foto, áudio ou reação), ignora
        if not message_body:
            return jsonify({"status": "ignored_no_text"}), 200

        sender_number = message_data.get("key", {}).get("remoteJid", "")
        print(f"Mensagem de texto recebida de {sender_number}: {message_body}")

        # Gera a resposta utilizando o Gemini com modelo alternativo para evitar instabilidade
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message_body,
            config={
                "system_instruction": SYSTEM_PROMPT,
            }
        )
            }
        )
        
        reply_text = response.text
        print(f"Resposta gerada pelo Gemini: {reply_text}")

        return jsonify({"status": "success", "reply": reply_text}), 200

    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


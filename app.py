import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Configuração do Gemini API usando a nova SDK oficial (google-genai)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Prompt do Sistema Versátil para Demonstração
SYSTEM_PROMPT = """
Você é um assistente virtual inteligente, prestativo e profissional, especializado em atendimento automatizado via WhatsApp.
Seu objetivo é responder aos clientes de forma clara, empática e objetiva, demonstrando a eficiência da automação com Inteligência Artificial.
Mantenha um tom cordial e adaptado para conversas de chat.
"""

@app.route("/", methods=["GET"])
def home():
    return "TestBot WhatsApp Rodando com Sucesso! 🚀", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("Dados recebidos da Evolution API:", data)
        
        # Extrai a mensagem e o remetente com base no padrão da Evolution API
        message_data = data.get("data", {})
        message_body = ""
        
        # Tenta pegar o texto da mensagem dependendo do formato do evento
        if "message" in message_data:
            msg_content = message_data.get("message", {})
            message_body = msg_content.get("conversation") or msg_content.get("extendedTextMessage", {}).get("text", "")
        
        # Se não achou na estrutura interna, tenta pegar direto no corpo
        if not message_body:
            message_body = message_data.get("body", "")

        sender_number = message_data.get("key", {}).get("remoteJid", "")
        
        # Ignora mensagens vazias ou enviadas pelo próprio bot
        if not message_body or message_data.get("key", {}).get("fromMe", False):
            return jsonify({"status": "ignored"}), 200

        print(f"Mensagem recebida de {sender_number}: {message_body}")

        # Gera a resposta utilizando o Gemini (modelo flash rápido)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message_body,
            config={
                "system_instruction": SYSTEM_PROMPT,
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
import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import httpx # For verify=False with OpenAI client
from flask_cors import CORS # CORS support for frontend interaction

load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for all origins and all routes

# Retrieve environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx.Client(verify=False))

# Helper function to generate game design document using LLM
def generate_game_design_document(game_idea: str, user_inputs: dict = None):
    """
    LLM kullanarak kullanıcıdan gelen oyun fikrini yapılandırılmış bir oyun tasarım dökümanına dönüştürür.
    """
    # Detaylı bir prompt ile LLM'den belirli bir JSON yapısı istiyoruz.
    # Bu JSON yapısı, diğer ajanların (Game Logic, Asset Planner) doğrudan kullanabileceği formatta olmalı.
    prompt = (
        f"Sen bir Oyun Tasarım Uzmanı AI ajanısın. Sana bir kullanıcıdan gelen oyun fikri verilecek. "
        f"Bu fikri analiz et ve aşağıda belirtilen JSON formatında detaylı bir Oyun Tasarım Dökümanı oluştur. "
        f"Cevabını **yalnızca JSON formatında** döndür, ek metin veya açıklama ekleme.\n\n"
        f"Oyun fikri: \"{game_idea}\"\n"
        f"Kullanıcıdan ek girdiler (varsa): {json.dumps(user_inputs, indent=2) if user_inputs else '{}'}\n\n"
        f"Oyun Tasarım Dökümanı Formatı (JSON):\n"
        f"```json\n"
        f"{{\n"
        f'  "game_title": "Oyun Adı (LLM tarafından önerilen)",\n'
        f'  "genre": "Oyun Türü (örn: Endless Runner, Puzzle, RPG)",\n'
        f'  "core_mechanics": [\n'
        f'    "Mekanik 1 (örn: Zıplama)",\n'
        f'    "Mekanik 2 (örn: Çarpışma Tespiti)"\n'
        f'  ],\n'
        f'  "game_flow": "Oyunun başlangıcından sonuna kadar olan akışın kısa özeti.",\n'
        f'  "characters": [\n'
        f'    {{"name": "Karakter Adı", "description": "Karakterin kısa tanımı"}}\n'
        f'  ],\n'
        f'  "enemies": [\n'
        f'    {{"name": "Düşman Adı", "description": "Düşmanın kısa tanımı", "behavior": "Davranışı"}}\n'
        f'  ],\n'
        f'  "scoring_system": "Puanlama sisteminin açıklaması (örn: Toplanan altınlar, düşman öldürme)",\n'
        f'  "controls": "Kontrollerin açıklaması (örn: Ekrana dokunma ile zıpla)",\n'
        f'  "target_audience": "Hedef kitle (örn: 8-12 yaş arası çocuklar)",\n'
        f'  "unique_selling_points": [\n'
        f'    "Oyunun benzersiz özellikleri"\n'
        f'  ],\n'
        f'  "initial_level_design_notes": "İlk seviye için kısa tasarım notları."\n'
        f"}}\n"
        f"```\n"
        f"JSON Çıktısı:"
    )

    try:
        chat_completion = openai_client.chat.completions.create(
            model="gpt-4o", # Yaratıcı ve yapılandırılmış çıktı için GPT-4o idealdir
            messages=[
                {"role": "system", "content": "You are an expert Game Designer AI. Your task is to analyze user game ideas and generate a detailed Game Design Document in JSON format. Provide only the JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # Yaratıcılığa izin vermek için biraz daha yüksek sıcaklık
            response_format={"type": "json_object"} # JSON çıktı formatını zorla
        )
        raw_json_output = chat_completion.choices[0].message.content.strip()
        print(f"LLM'den gelen raw JSON: {raw_json_output}") 
        
        # Eğer yanıt markdown içinde gelirse temizle
        if raw_json_output.startswith("```json"):
            raw_json_output = raw_json_output.replace("```json", "").replace("```", "").strip()

        parsed_output = json.loads(raw_json_output)
        return parsed_output
    except Exception as e:
        print(f"Oyun tasarım dökümanı oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Oyun tasarım dökümanı oluşturulurken hata: {e}"}

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "game-design-expert-agent"}), 200

# Main endpoint to generate game design
@app.route("/generate-game-design", methods=["POST"])
def generate_game_design_endpoint():
    data = request.get_json()
    game_idea = data.get("gameIdea")
    user_inputs = data.get("userInputs", {}) # Opsiyonel: karakter konseptleri, düşman çizimleri gibi ek girdiler

    if not game_idea:
        return jsonify({"error": "Oyun fikri (gameIdea) gerekli."}), 400

    print(f"Oyun fikri alındı: {game_idea}")

    try:
        game_design_doc = generate_game_design_document(game_idea, user_inputs)
        return jsonify(game_design_doc), 200
    except Exception as e:
        print(f"Oyun tasarım dökümanı oluşturulurken genel bir hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Oyun tasarım dökümanı oluşturulurken hata oluştu: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


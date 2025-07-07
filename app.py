import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/generate-game-design", methods=["POST"])
def generate_game_design():
    data = request.get_json()
    game_idea = data.get("gameIdea")
    user_inputs = data.get("userInputs", {})

    if not game_idea:
        return jsonify({"error": "gameIdea alanı zorunludur"}), 400

    prompt = (
        f"Sen bir Oyun Tasarım Uzmanı AI ajanısın. "
        f"Sana bir oyun fikri verilecek. Bu fikri analiz et ve oyun türüne göre "
        f"gereksiz alanları çıkartarak yalnızca ihtiyaç duyulan alanları içeren "
        f"detaylı bir JSON oyun tasarım dokümanı hazırla.\n\n"

        f"Eğer bu oyunda örneğin düşman yoksa, enemies alanını hiç ekleme. "
        f"Aynı şekilde scoring, controls veya initial_level_design_notes da oyun fikrine göre şekillenmeli. "
        f"Boş veya gereksiz alanlar eklenmesin.\n\n"
        f"Oyun fikri: \"{game_idea}\"\n"
        f"Kullanıcı ek girdileri: {json.dumps(user_inputs, indent=2)}\n\n"
        f"Çıktıyı **sadece saf JSON olarak** döndür."
    )

    print("🧠 LLM Prompt gönderiliyor:\n", prompt)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Sen uzman bir oyun tasarım AI ajansısın."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6
    )

    raw_output = response.choices[0].message.content.strip()
    print("\n✅ Gelen raw output:\n", raw_output)

    try:
        parsed_output = json.loads(raw_output)
    except json.JSONDecodeError as e:
        return jsonify({
            "error": f"LLM JSON çıktısı parse edilemedi: {e}",
            "raw_output": raw_output
        }), 500

    return jsonify(parsed_output), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "game-design-expert-agent"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

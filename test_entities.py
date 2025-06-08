from transformers import pipeline

print("Зареждане на NER модела...")
# Зареждаме Named Entity Recognition модел
ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", aggregation_strategy="simple")
print("NER модел зареден!")

# Тестов криптовалутен текст
crypto_text = """
Elon Musk announced Tesla will accept Bitcoin payments again. 
Coinbase and Binance reported record trading volumes. 
Ethereum founder Vitalik Buterin spoke at the London conference yesterday.
"""

print("\n=== ТЕСТВАНЕ НА ENTITY RECOGNITION ===")
print(f"Текст: {crypto_text}")

# Намираме entities
entities = ner_pipeline(crypto_text)

print("\nОткрити entities:")
for entity in entities:
    print(f"Текст: '{entity['word']}' | Тип: {entity['entity_group']} | Увереност: {entity['score']:.3f}")
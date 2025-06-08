from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

print("Зареждане на sentiment analysis модела...")

# Зареждаме FinBERT модела - специално обучен за финансови текстове
model_name = "ProsusAI/finbert"
sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)

print("Моделът е зареден успешно!")

# Тестови криптовалутни текстове
test_texts = [
    "Bitcoin price surged to new all-time highs today",
    "Major crypto exchange faces regulatory investigation",
    "Ethereum network upgrade completed successfully"
]

print("\n=== ТЕСТВАНЕ НА SENTIMENT ANALYSIS ===")

for i, text in enumerate(test_texts, 1):
    result = sentiment_pipeline(text)[0]
    print(f"\nТекст {i}: {text}")
    print(f"Sentiment: {result['label']}")
    print(f"Confidence: {result['score']:.3f}")
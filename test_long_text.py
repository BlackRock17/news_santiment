from transformers import pipeline

# Зареждаме модела
sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")

# Примерен дълъг криптовалутен текст (симулира статия)
long_article = """
Bitcoin experienced significant price volatility this week, with the cryptocurrency 
reaching new monthly highs before pulling back slightly. Market analysts suggest 
that institutional adoption continues to drive long-term growth, despite short-term 
fluctuations. Several major companies have announced plans to integrate Bitcoin 
payments into their platforms.

The recent regulatory clarity from government officials has boosted investor confidence. 
Many believe this marks a turning point for cryptocurrency acceptance in traditional 
finance. Trading volumes have increased substantially, indicating growing interest 
from retail and institutional investors alike.

However, some experts warn about potential risks associated with rapid price movements. 
They recommend cautious investment approaches and proper risk management strategies. 
The cryptocurrency market remains highly speculative and volatile.
"""

print("Анализиране на дълъг текст...")
result = sentiment_pipeline(long_article)[0]

print(f"\nДължина на текста: {len(long_article)} символа")
print(f"Sentiment: {result['label']}")
print(f"Confidence: {result['score']:.3f}")
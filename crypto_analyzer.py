from sentiment_analyzer import SentimentAnalyzer
from entity_analyzer import EntityAnalyzer


class CryptoAnalyzer:
    def __init__(self):
        print("=== ИНИЦИАЛИЗИРАНЕ НА CRYPTO ANALYZER ===")
        self.sentiment_analyzer = SentimentAnalyzer()
        self.entity_analyzer = EntityAnalyzer()
        print("Всички модели са заредени!")

    def analyze_crypto_text(self, text):
        """Прави пълен анализ на криптовалутен текст"""
        print("Започвам пълен анализ...")

        # Sentiment анализ
        sentiment_result = self.sentiment_analyzer.analyze(text)

        # Entity анализ
        entities_result = self.entity_analyzer.extract_entities(text)

        # Комбинираме резултатите
        full_analysis = {
            'text_info': {
                'length': sentiment_result['text_length'],
                'preview': text[:100] + "..." if len(text) > 100 else text
            },
            'sentiment': {
                'label': sentiment_result['sentiment'],
                'confidence': sentiment_result['confidence']
            },
            'entities': entities_result,
            'summary': self._generate_summary(sentiment_result, entities_result)
        }

        return full_analysis

    def _generate_summary(self, sentiment, entities):
        """Генерира кратко резюме на анализа"""
        # Броим entities
        total_entities = sum(len(items) for items in entities.values())
        crypto_count = len(entities['crypto_related'])
        person_count = len(entities['persons'])

        summary = f"Sentiment: {sentiment['sentiment']} ({sentiment['confidence']:.2f}). "
        summary += f"Намерени {total_entities} entities"

        if crypto_count > 0:
            summary += f", включително {crypto_count} crypto-related"
        if person_count > 0:
            summary += f", {person_count} persons"

        return summary


# Тест с реалистична криптовалутна статия
if __name__ == "__main__":
    analyzer = CryptoAnalyzer()

    sample_article = """
    Bitcoin reached a new monthly high yesterday as institutional investors 
    continue to show strong interest. Elon Musk's recent comments about 
    cryptocurrency adoption have boosted market confidence. Meanwhile, 
    Ethereum developers announced successful completion of the latest network 
    upgrade in London. Major exchanges like Coinbase and Binance reported 
    record trading volumes for both Bitcoin and Ethereum.
    """

    print("\n" + "=" * 50)
    print("ТЕСТВАНЕ НА ПЪЛНИЯ ANALYZER")
    print("=" * 50)

    result = analyzer.analyze_crypto_text(sample_article)

    print(f"\nРезюме: {result['summary']}")
    print(f"\nSentiment: {result['sentiment']['label']} (увереност: {result['sentiment']['confidence']})")

    print("\nНамерени entities:")
    for category, items in result['entities'].items():
        if items:
            print(f"  {category}: {[item['text'] for item in items]}")
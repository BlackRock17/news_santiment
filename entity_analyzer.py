from transformers import pipeline


class EntityAnalyzer:
    def __init__(self):
        print("Зареждане на NER модела...")
        self.ner_pipeline = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english",
            aggregation_strategy="simple"  # Това трябва да помогне с токените
        )
        print("NER модел зареден!")

        # Известни криптовалути
        self.crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'binance', 'bnb',
            'cardano', 'ada', 'solana', 'sol', 'polkadot', 'dot',
            'chainlink', 'link', 'dogecoin', 'doge', 'ripple', 'xrp'
        ]

    def _is_crypto_related(self, text):
        """Проверява дали текстът е свързан с криптовалути"""
        text_lower = text.lower()
        return any(crypto in text_lower for crypto in self.crypto_keywords)

    def _clean_entity_text(self, text):
        """Почиства entity текста от BERT токени"""
        # Премахваме ## префикси и свързваме разделени думи
        return text.replace('##', '')

    def extract_entities(self, text):
        """Извлича entities от текст"""
        raw_entities = self.ner_pipeline(text)

        # Групираме по тип
        result = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'crypto_related': [],
            'other': []
        }

        for entity in raw_entities:
            cleaned_text = self._clean_entity_text(entity['word'])
            entity_info = {
                'text': cleaned_text,
                'confidence': round(entity['score'], 3),
                'original': entity['word']  # За debugging
            }

            # Категоризиране
            if self._is_crypto_related(cleaned_text):
                result['crypto_related'].append(entity_info)
            elif entity['entity_group'] == 'PER':
                result['persons'].append(entity_info)
            elif entity['entity_group'] == 'ORG':
                result['organizations'].append(entity_info)
            elif entity['entity_group'] == 'LOC':
                result['locations'].append(entity_info)
            else:
                result['other'].append(entity_info)

        return result


# Тест с по-сложен текст
if __name__ == "__main__":
    analyzer = EntityAnalyzer()

    test_text = """
    Elon Musk announced that Tesla will resume Bitcoin payments. 
    Ethereum founder Vitalik Buterin spoke at the conference in London.
    Binance and Coinbase reported increased trading volumes for Cardano and Solana.
    """

    entities = analyzer.extract_entities(test_text)

    print("\n=== ПОДОБРЕНИ РЕЗУЛТАТИ ===")
    for category, items in entities.items():
        if items:
            print(f"\n{category.upper()}:")
            for item in items:
                print(f"  - {item['text']} (увереnost: {item['confidence']})")
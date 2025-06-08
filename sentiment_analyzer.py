from transformers import pipeline


class SentimentAnalyzer:
    def __init__(self):
        print("Зареждане на sentiment модела...")
        self.sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        print("Модел зареден!")
        # Максимална дължина на токени за модела
        self.max_length = 512

    def _truncate_text(self, text, max_tokens=400):
        """Съкращава текста ако е твърде дълъг"""
        words = text.split()
        if len(words) <= max_tokens:
            return text

        # Вземаме първите и последните думи за да запазим контекста
        first_part = words[:max_tokens // 2]
        last_part = words[-(max_tokens // 2):]

        truncated = " ".join(first_part) + " ... " + " ".join(last_part)
        return truncated

    def analyze(self, text):
        """Анализира sentiment на даден текст"""
        # Проверяваме и съкращаваме ако е необходимо
        original_length = len(text)
        processed_text = self._truncate_text(text)
        was_truncated = len(processed_text) < original_length

        try:
            result = self.sentiment_pipeline(processed_text)[0]
            return {
                'text_length': original_length,
                'sentiment': result['label'],
                'confidence': round(result['score'], 3),
                'was_truncated': was_truncated,
                'processed_length': len(processed_text)
            }
        except Exception as e:
            # Ако все още има проблем, използваме само първите 200 думи
            short_text = " ".join(text.split()[:200])
            result = self.sentiment_pipeline(short_text)[0]
            return {
                'text_length': original_length,
                'sentiment': result['label'],
                'confidence': round(result['score'], 3),
                'was_truncated': True,
                'processed_length': len(short_text),
                'note': 'Текстът беше силно съкратен поради ограничения на модела'
            }

    def analyze_multiple(self, texts):
        """Анализира списък от текстове"""
        results = []
        for i, text in enumerate(texts, 1):
            print(f"Анализиране на текст {i}/{len(texts)}...")
            result = self.analyze(text)
            results.append(result)
        return results


# Тест с дълъг текст
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    # Тест с много дълъг текст
    long_text = "Bitcoin " * 300  # Симулира много дълъг текст
    result = analyzer.analyze(long_text)

    print(f"Резултат: {result}")
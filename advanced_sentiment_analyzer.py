from transformers import pipeline


class AdvancedSentimentAnalyzer:
    def __init__(self):
        print("Зареждане на summarization модел...")
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        print("Зареждане на sentiment модел...")
        self.sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")

        print("Модели заредени!")

        # ПРАВИЛНИ лимити базирани на токени
        self.sentiment_max_words = 300  # ~450 токена (безопасно под 512)
        self.target_summary_words = 280  # Цел за summarization
        self.min_summary_words = 50  # Минимум думи
        self.short_text_limit = 320  # Кога да НЕ правим summarization

    def _count_words(self, text):
        """Брои думите в текста"""
        return len(text.split())

    def _estimate_tokens(self, text):
        """Приблизително изчисляване на токени"""
        words = self._count_words(text)
        return int(words * 1.4)  # Консервативна оценка

    def _calculate_optimal_summary_length(self, original_word_count):
        """Изчислява оптималната дължина на summary"""

        if original_word_count <= self.short_text_limit:
            return None  # Не се нуждае от summarization

        # Градуално увеличаване, но винаги под лимита
        if original_word_count <= 500:
            target_length = 250
        elif original_word_count <= 1000:
            target_length = 270
        else:
            target_length = 290

        return min(target_length, self.sentiment_max_words)

    def _safe_truncate_for_sentiment(self, text):
        """Безопасно съкращава текст за sentiment модела"""
        words = text.split()
        if len(words) <= self.sentiment_max_words:
            return text, len(words)

        print(f"ПРЕДУПРЕЖДЕНИЕ: Текст е {len(words)} думи, съкращавам до {self.sentiment_max_words}")
        truncated = " ".join(words[:self.sentiment_max_words])
        return truncated, self.sentiment_max_words

    def _summarize_text(self, text, target_length):
        """Summarization с гарантирана безопасност"""
        try:
            # Безопасно подготвяме за BART
            words = text.split()
            if len(words) > 600:  # BART лимит
                safe_text = " ".join(words[:600])
            else:
                safe_text = text

            # Консервативни BART параметри
            max_tokens = min(int(target_length * 1.1), 150)
            min_tokens = max(int(target_length * 0.4), 25)

            print(f"BART: input {len(safe_text.split())} думи → target {target_length} думи")

            summary_result = self.summarizer(
                safe_text,
                max_length=max_tokens,
                min_length=min_tokens,
                do_sample=False
            )

            summary_text = summary_result[0]['summary_text']

            # Гарантираме че не надвишаваме лимита
            safe_summary, actual_words = self._safe_truncate_for_sentiment(summary_text)

            print(f"Summary готов: {actual_words} думи")
            return safe_summary, actual_words

        except Exception as e:
            print(f"BART грешка: {e}. Fallback метод...")

            # Fallback: Smart truncation
            sentences = text.split('.')
            if len(sentences) > 4:
                # Първите 60% + последните 40% от изреченията
                first_part = int(len(sentences) * 0.6)
                selected = sentences[:first_part] + sentences[-2:]
                fallback_text = '. '.join([s.strip() for s in selected if s.strip()])
            else:
                fallback_text = text

            # Гарантираме безопасност
            safe_fallback, actual_words = self._safe_truncate_for_sentiment(fallback_text)
            print(f"Fallback готов: {actual_words} думи")
            return safe_fallback, actual_words

    def analyze(self, text):
        """Безопасен анализ с гарантирани лимити"""
        original_word_count = self._count_words(text)
        estimated_tokens = self._estimate_tokens(text)

        print(f"Input: {original_word_count} думи (~{estimated_tokens} токена)")

        # Проверяваме дали се нуждае от summarization
        target_summary_length = self._calculate_optimal_summary_length(original_word_count)

        if target_summary_length is None:
            print("→ Директен анализ")
            # Дори за "кратки" текстове проверяваме безопасността
            processed_text, processed_word_count = self._safe_truncate_for_sentiment(text)
            used_summarization = False
            compression_ratio = 1.0 if processed_word_count == original_word_count else round(
                original_word_count / processed_word_count, 1)

        else:
            print(f"→ Summarization до {target_summary_length} думи")
            processed_text, processed_word_count = self._summarize_text(text, target_summary_length)
            used_summarization = True
            compression_ratio = round(original_word_count / processed_word_count, 1)

        final_tokens = self._estimate_tokens(processed_text)
        print(f"Обработен: {processed_word_count} думи (~{final_tokens} токена)")

        # Sentiment анализ
        try:
            sentiment_result = self.sentiment_pipeline(processed_text)[0]

            result = {
                'text_info': {
                    'original_word_count': original_word_count,
                    'processed_word_count': processed_word_count,
                    'estimated_tokens': final_tokens,
                    'compression_ratio': f"{compression_ratio}:1"
                },
                'processing': {
                    'used_summarization': used_summarization,
                    'method': 'summarization' if used_summarization else 'direct/truncated',
                    'efficiency': f"{processed_word_count}/{self.sentiment_max_words} думи ({int(processed_word_count / self.sentiment_max_words * 100)}%)",
                    'token_safe': final_tokens <= 512
                },
                'sentiment': {
                    'label': sentiment_result['label'],
                    'confidence': round(sentiment_result['score'], 3)
                }
            }

            if used_summarization:
                result['processing']['summary_preview'] = processed_text[:120] + "..."

            return result

        except Exception as e:
            return {
                'error': f"Sentiment грешка: {str(e)}",
                'text_info': {
                    'original_word_count': original_word_count,
                    'processed_word_count': processed_word_count
                }
            }


# ТЕСТ с правилни размери
if __name__ == "__main__":
    analyzer = AdvancedSentimentAnalyzer()

    test_cases = [
        ("Кратък", """Sui (SUI) has dropped in the past week as the crypto market rally that started in late April has cooled off a bit but has still managed to leave the token in a much better place to eye a retest of its all-time high.
This layer-1 blockchain had a great first quarter. A report from Messari highlighted that average daily DEX volumes on Sui reached a record of $304.3 million. This represented a 315.7% increase compared to the same period a year ago.
Meanwhile, the total value locked (TVL) in its DeFi ecosystem grew by 35% compared to the previous quarter and currently stands at 544.1 million SUI.
Expressing TVL values in SUI rather than USD helps offset the negative or positive impact that price appreciation or depreciation of the SUI token can cause in this metric.
Meanwhile, the network’s stablecoin market cap increased by nearly 57% compared to the previous quarter and currently sits at $580.50 million.
Despite the Cetus incident, these metrics indicate rapid ecosystem growth and favor a bullish Sui price prediction.
Sui Price Prediction: SUI Could Retest Its All-Time High If This Key Support Holds
The daily chart shows that Sui recently broke its bullish structure as it dropped below its second-best higher high of around $3.6.
However, the token has found strong support at the $3 level. This is a key psychological threshold as well that late buyers could have picked as an ideal entry after a much-needed pullback from SUI’s latest rally.
The Relative Strength Index (RSI) currently sits at 43, meaning that bears are in control of the price action and negative momentum has accelerated.
After its bounce from the $3 level, Sui has been performing positively for three days in a row, counting this session’s strong recovery from daily lows.
If the price breaks out of its descending price channel, this would confirm a bullish outlook. The market may retest the $3 level again to raise the necessary liquidity and then prepare for the next leg up, which could take SUI from $3 to $5.
This jump would resemble the late April rally, which pushed SUI from less than $2 to $4 in just a month.
The war between smart contracts platform continue and one crypto presale stands to gain from Solana’s dominance of the meme coin market. Solaxy (SOLX), a layer-two scaling solution, has raised more than $40 million since its ICO kicked off in December 2024.
Solaxy (SOLX) Gives the Community 14 More Days to Invest
Solaxy (SOLX) is a promising layer-2 project for the Solana network that solves the congestion issues that this blockchain has experienced during peak usage periods.
The developing team has made significant progress in launching the L2 including the release of a block explorer for the Solaxy testnet that allows investors to check the blockchain’s performance in real time.
Once Solaxy starts to be adopted by wallets and exchanges, the demand for its utility token, $SOLX, will skyrocket. On top of its upside potential, the project offers staking rewards of 93% to investors who lock up their tokens to secure the L2.
To buy $SOLX at its discounted price before the presale ends, head to the Solaxy website and connect your wallet (e.g. Best Wallet). You can either swap USDT or SOL for this token or use a bank card to make your investment.""", 1)
        # ("Среден", "Bitcoin analysis. " * 50, 2),  # ~100 думи
        # ("По-дълъг", "Bitcoin market report. " * 150, 3),  # ~450 думи
        # ("Много дълъг", "Detailed analysis. " * 400, 4)  # ~800 думи
    ]

    for name, text, num in test_cases:
        print(f"\n{'=' * 10} ТЕСТ {num}: {name.upper()} {'=' * 10}")
        result = analyzer.analyze(text)

        if 'error' not in result:
            print(f"Думи: {result['text_info']['original_word_count']} → {result['text_info']['processed_word_count']}")
            print(f"Токени: ~{result['text_info']['estimated_tokens']} (safe: {result['processing']['token_safe']})")
            print(f"Метод: {result['processing']['method']}")
            print(f"Ефективност: {result['processing']['efficiency']}")
            print(f"Sentiment: {result['sentiment']['label']} ({result['sentiment']['confidence']})")
        else:
            print(f"Грешка: {result['error']}")

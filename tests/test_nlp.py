from src.models.nlp import NewsSentimentAnalyzer

def test_nlp():
    analyzer = NewsSentimentAnalyzer()
    
    print("--- Testing NLP Module ---\n")
    
    sample_headlines = [
        "Reliance Industries reports Q3 profit surge.", 
        "TCS shares fall 5% on weak guidance.",
        "Nifty hits all-time high, Sensex crosses 80k!",
        "HDFC Bank announces dividend.",
        "Inflation worries grip market, stocks tumble."
    ]
    
    for headline in sample_headlines:
        score = analyzer.get_sentiment(headline)
        print(f"Headline: {headline}")
        print(f"Sentiment Score: {score}\n")

if __name__ == "__main__":
    test_nlp()

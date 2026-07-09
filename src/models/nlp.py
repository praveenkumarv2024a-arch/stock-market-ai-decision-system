from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

class NewsSentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
    def get_sentiment(self, text):
        """
        Returns a compound sentiment score between -1 and 1.
        Uses VADER (better for social media/short text) and TextBlob average.
        """
        if not text:
            return 0.0
            
        # VADER score
        vader_score = self.vader.polarity_scores(text)['compound']
        
        # TextBlob score
        blob_score = TextBlob(text).sentiment.polarity
        
        # Weighted average (VADER is usually better for finance/news headlines)
        final_score = (0.7 * vader_score) + (0.3 * blob_score)
        return final_score

if __name__ == "__main__":
    analyzer = NewsSentimentAnalyzer()
    print("Test 1 (Positive):", analyzer.get_sentiment("Reliance Industries reports record profits, stock soars."))
    print("Test 2 (Negative):", analyzer.get_sentiment("Market crashes as inflation fears rise, Sensex down 500 points."))
    print("Test 3 (Neutral):", analyzer.get_sentiment("Reliance to hold AGM on Friday."))

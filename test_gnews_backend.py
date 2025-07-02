import sys
import json
from Gnews_backend import get_news_summaries

def main():
    print("Test Gnews_backend: HR News Summarizer\n")
    print("Available topics:")
    topics = [
        "hr strategy and leadership",
        "workforce compliance and regulation",
        "talent acquisition and labor trends",
        "compensation, benefits and rewards",
        "people development and culture"
    ]
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")
    print()
    topic = input("Enter a topic from the list above: ").strip().lower()
    if topic not in topics:
        print("Invalid topic. Exiting.")
        sys.exit(1)
    user_id = input("Enter a user ID (optional): ").strip() or None
    # Always use the correct path to prompts.json in the HR folder
    prompt_file = "c:/Users/kaisa/OneDrive/Desktop/Ai projects/HR/prompts.json"
    model = input("Enter OpenAI model (default: gpt-4-turbo): ").strip() or "gpt-4-turbo"
    print("\nFetching and summarizing news...\n")
    result = get_news_summaries(topic, user_id, prompt_file, model)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

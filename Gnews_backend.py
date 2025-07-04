import os
import json
import logging
import requests
import feedparser
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
from dateutil import parser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY not found in environment variables.")

# Initialize OpenAI client
try:
    openai_client = OpenAI(api_key=openai_api_key)
except OpenAIError as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    raise RuntimeError(f"Invalid OpenAI API key or configuration: {e}")

prompt_cache = {}
news_cache = {}
summary_cache = {}
conversation_history = {}

def load_prompt(filepath="prompts.json", prompt_key="NEWS_SUMMARIZER"):
    cache_key = f"{filepath}:{prompt_key}"
    if cache_key in prompt_cache:
        return prompt_cache[cache_key]
    try:
        with open(filepath, "r") as file:
            data = json.load(file)
            prompt = data[prompt_key]
            prompt_cache[cache_key] = prompt
            return prompt
    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        raise RuntimeError(f"Error loading prompt: {e}")

def sanitize_input(text: str) -> str:
    text = re.sub(r'[^\w\s.,!?]', '', text)
    return ' '.join(text.split())

def get_relative_time(published_at):
    pub_time = parser.parse(published_at)
    now = datetime.now(pub_time.tzinfo) if pub_time.tzinfo else datetime.now()
    time_diff = now - pub_time
    if time_diff < timedelta(minutes=60):
        minutes = int(time_diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif time_diff < timedelta(hours=24):
        hours = int(time_diff.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = int(time_diff.total_seconds() / 86400)
        return f"{days}d ago"

def get_topic_tag(matched_topic, article_content):
    topic_map = {
        "hr strategy and leadership": "Leadership",
        "workforce compliance and regulation": "Compliance",
        "talent acquisition and labor trends": "Talent",
        "compensation, benefits and rewards": "Compensation",
        "people development and culture": "Culture"
    }
    default_tag = topic_map.get(matched_topic, "General")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an HR expert. Assign one tag from [Leadership, Compliance, Talent, Compensation, Culture] based on the article content."},
                {"role": "user", "content": f"Analyze this content and assign a tag: {article_content[:500]}"}
            ],
            max_tokens=10
        )
        detected_tag = response.choices[0].message.content.strip()
        return detected_tag if detected_tag in topic_map.values() else default_tag
    except Exception as e:
        logger.warning(f"Failed to detect tag: {e}")
        return default_tag

# RSS feed sources for each HR topic (with source names)
RSS_FEEDS = {
    "hr strategy and leadership": [
        {"name": "HR Executive", "url": "https://hrexecutive.com/feed/"},
        {"name": "Harvard Business Review - Leadership", "url": "https://hbr.org/feed/section/leadership"},
        {"name": "HR Dive - Strategy", "url": "https://www.hrdive.com/rss/strategy/"},
        {"name": "SHRM - Executive HR", "url": "https://www.shrm.org/rss/feed.aspx?category=executive"},
        {"name": "HR Grapevine", "url": "https://www.hrgrapevine.com/rss"}
    ],
    "workforce compliance and regulation": [
        {"name": "EEOC Newsroom", "url": "https://www.eeoc.gov/newsroom/rss.xml"},
        {"name": "HR Dive - Compliance", "url": "https://www.hrdive.com/rss/compliance/"},
        {"name": "SHRM - Legal Issues", "url": "https://www.shrm.org/rss/feed.aspx?category=legal"},
        {"name": "Law360 - Employment", "url": "https://www.law360.com/employment-authority/rss"}
    ],
    "talent acquisition and labor trends": [
        {"name": "ERE Media", "url": "https://www.eremedia.com/rss"},
        {"name": "HR Dive - Talent Acquisition", "url": "https://www.hrdive.com/rss/talent-acquisition/"},
        {"name": "Workology - Recruiting", "url": "https://workology.com/category/recruiting/feed/"},
        {"name": "Undercover Recruiter", "url": "https://theundercoverrecruiter.com/feed/"}
    ],
    "compensation, benefits and rewards": [
        {"name": "BenefitsPRO", "url": "https://www.benefitspro.com/rss/"},
        {"name": "SHRM - Compensation & Benefits", "url": "https://www.shrm.org/rss/feed.aspx?category=compensation"},
        {"name": "HR Dive - Benefits", "url": "https://www.hrdive.com/rss/benefits/"}
    ],
    "people development and culture": [
        {"name": "Chief Learning Officer", "url": "https://www.chieflearningofficer.com/feed/"},
        {"name": "HR Bartender", "url": "https://www.hrbartender.com/feed/"},
        {"name": "Workology - HR Development", "url": "https://workology.com/category/hr/feed/"}
    ]
}

@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=1, max=5))
def fetch_news(topic: str, max_results=15, days_lookback=30, per_day=True, target_date=None) -> list:
    """
    Fetch news articles for a topic, filtered by date.
    - days_lookback: Only include articles from the last N days (default 7).
    - per_day: If True, fetch all articles from today (or target_date if provided), ignoring max_results.
    - target_date: If per_day is True, fetch articles from this date (YYYY-MM-DD), else today.
    """
    feeds = RSS_FEEDS.get(topic.lower(), [])
    articles = []
    seen_titles = set()
    now = datetime.now()
    # Helper to make a datetime offset-naive or offset-aware to match published_dt
    def match_tz(dt, ref_dt):
        if dt.tzinfo and not ref_dt.tzinfo:
            return dt.replace(tzinfo=None)
        elif not dt.tzinfo and ref_dt.tzinfo:
            return dt.replace(tzinfo=ref_dt.tzinfo)
        return dt

    if per_day:
        if target_date:
            try:
                day_start = datetime.strptime(target_date, "%Y-%m-%d")
            except Exception:
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
    else:
        lookback_start = now - timedelta(days=days_lookback)
    for feed in feeds:
        feed_name = feed["name"]
        feed_url = feed["url"]
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries:
                title = entry.get("title", "").strip()
                if not title or title.lower() in seen_titles:
                    continue
                published_str = entry.get("published", None)
                if published_str:
                    try:
                        published_dt = parser.parse(published_str)
                    except Exception:
                        published_dt = now
                else:
                    published_dt = now
                # Date filtering (handle tz-aware/naive)
                if per_day:
                    ds = match_tz(day_start, published_dt)
                    de = match_tz(day_end, published_dt)
                    if not (ds <= published_dt < de):
                        continue
                else:
                    lbs = match_tz(lookback_start, published_dt)
                    if published_dt < lbs:
                        continue
                seen_titles.add(title.lower())
                article = {
                    "title": title,
                    "url": entry.get("link", ""),
                    "description": entry.get("summary", ""),
                    "content": entry.get("summary", ""),
                    "source": {"name": feed_name, "feed_url": feed_url},
                    "publishedAt": published_dt.isoformat()
                }
                articles.append(article)
                if not per_day and len(articles) >= max_results:
                    break
            if not per_day and len(articles) >= max_results:
                break
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            continue
    if not articles:
        logger.warning(f"No articles found for topic: {topic} in RSS feeds.")
    return articles

@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=1, max=5))
def summarize_article(article: dict, prompt: str, model: str) -> str:
    content = f"{article.get('title', '')}\n{article.get('description', '')}\n{article.get('content', '')}"
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Summarize the following news article in 2-3 sentences from an HR expert perspective:\n{content}"}
    ]
    try:
        if model is None or model.strip() == '' or model == 'gpt-3.5-turbo':
            model = 'gpt-4-turbo'
        logger.info(f"Using OpenAI model: {model}")
        assistant_reply = ""
        response_stream = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=150,
            stream=True
        )
        for chunk in response_stream:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    assistant_reply += content
        return assistant_reply.strip()
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise

def get_news_summaries(user_input: str, user_id: str = None, prompt_file: str = "prompts.json", model: str = "gpt-4-turbo") -> dict:
    if not user_input or not user_input.strip():
        logger.warning("Empty or invalid input received.")
        return {"status": "error", "message": "Please provide a valid topic or query."}
    query = sanitize_input(user_input)
    if not query:
        logger.warning("Input is empty after sanitization.")
        return {"status": "error", "message": "Please provide a valid topic or query."}
    allowed_topics = [
        "hr strategy and leadership",
        "workforce compliance and regulation",
        "talent acquisition and labor trends",
        "compensation, benefits and rewards",
        "people development and culture"
    ]
    matched_topic = next((topic for topic in allowed_topics if topic.lower() in query.lower()), None)
    if not matched_topic:
        logger.warning(f"Input does not match allowed topics: {query}")
        return {"status": "error", "message": f"Please specify one of: {', '.join(allowed_topics)}"}
    cache_key = f"{matched_topic}:{datetime.now().strftime('%Y-%m-%d')}"
    if cache_key in news_cache:
        logger.info(f"Cache hit for news articles: {matched_topic}")
        articles = news_cache[cache_key]
        cached_articles = True
    else:
        articles = fetch_news(matched_topic)
        news_cache[cache_key] = articles
        cached_articles = False
        for key in list(news_cache.keys()):
            key_date = datetime.strptime(key.split(':')[-1], '%Y-%m-%d')
            if datetime.now() - key_date > timedelta(days=1):
                del news_cache[key]
    if not articles:
        return {"status": "error", "message": f"No articles found for topic: {matched_topic}"}
    try:
        summary_prompt = load_prompt(prompt_file, "NEWS_SUMMARIZER")
    except RuntimeError:
        return {"status": "error", "message": "Failed to load summarization prompt."}
    summaries = []
    for article in articles:
        article_key = f"{article.get('title', '')}:{matched_topic}"
        content = f"{article.get('title', '')}\n{article.get('description', '')}\n{article.get('content', '')}"
        if article_key in summary_cache:
            logger.info(f"Cache hit for article summary: {article.get('title', 'Unknown')}")
            summaries.append({
                "title": article.get("title", "No title"),
                "url": article.get("url", ""),
                "summary": summary_cache[article_key],
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt", datetime.now().isoformat()),
                "cached": True
            })
        else:
            try:
                summary = summarize_article(article, summary_prompt, model)
                summary_cache[article_key] = summary
                tag = get_topic_tag(matched_topic, content)
                summaries.append({
                    "title": article.get("title", "No title"),
                    "url": article.get("url", ""),
                    "summary": summary,
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "published_at": article.get("publishedAt", datetime.now().isoformat()),
                    "tag": tag,
                    "cached": False
                })
            except Exception as e:
                logger.error(f"Error summarizing article {article.get('title', 'Unknown')}: {e}")
                continue
    if user_id:
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        conversation_history[user_id].append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat(),
            "topic": matched_topic,
            "summaries": summaries
        })
        conversation_history[user_id] = conversation_history[user_id][-10:]
    logger.info(f"Generated summaries for topic: {matched_topic}")
    return {
        "status": "success",
        "topic": matched_topic,
        "articles": summaries,
        "cached_articles": cached_articles,
        "total_articles": len(summaries)
    }

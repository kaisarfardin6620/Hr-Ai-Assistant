# HR AI Assistant

A suite of robust, production-ready Python backend modules for various HR domains (Compensation, Compliance, Talent Acquisition, Organizational Development, and more). Each assistant leverages OpenAI’s GPT models to provide intelligent, context-aware responses for HR professionals and employees.

## Features

- Modular backend files for each HR domain (e.g., Compensation, Compliance, Talent Acquisition, etc.)
- Consistent structure: logging, input sanitization, caching, and error handling
- Conversation history per user for context-aware responses
- Easy integration with web APIs (Flask, Express.js, etc.)
- Supports both typed and transcribed (voice) input
- Ready for production deployment

## Project Structure

```
Compensation_backend.py
Compliance_backend.py
HR_Business_Partner_backend.py
HR_Strategy_backend.py
Learning_And_Development_backend.py
Organizational_Development_backend.py
Talent_Acquisition_backend.py
Total_Rewards_backend.py
Gnews_backend.py
Gnews.py
prompts.json
Compensation_Assistant.py
Compliance_Assistant.py
HR_Business_Partner_Assistant.py
HR_Strategy_Assistant.py
Learning_And_Development_Assistant.py
Organizational_Development_Assistant.py
Talent_Acquisition_Assistant.py
Total_Rewards_Assistant.py
requirements.txt
.env.example
```

## Setup

1. **Clone the repository and install dependencies:**
   ```bash
   git clone https://github.com/kaisarfardin6620/Hr-Ai-Assistant.git
   cd Hr-Ai-Assistant
   pip install -r requirements.txt
   ```

2. **Set up your environment variables:**
   - Create a `.env` file with your OpenAI API key:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```

3. **Run a backend module or API:**
   - Example (run a backend module):
     ```bash
     python Compensation_backend.py
     ```
   - Or integrate with your own Flask/FastAPI/Express.js API.

## Usage

- Import and call any backend function (e.g., `get_compensation_response`) in your API or application.
- Each function expects user input and (optionally) a user ID for conversation history.
- Responses are returned as structured dictionaries for easy integration.

### Example

```python
from Compensation_backend import get_compensation_response

result = get_compensation_response("What is the salary range for a data analyst?", user_id="user123")
print(result)
```

## API Integration

- Use your own API wrapper (Flask, FastAPI, etc.) to expose assistants as RESTful endpoints.
- Use `Gnews_backend.py` for HR news summaries from trusted RSS feeds.

## Extending

- Add new HR domains by following the existing backend file structure.
- Update `prompts.json` with new or refined system prompts.
- Contributions are welcome! Open an issue or submit a pull request.

## Troubleshooting

- Ensure your `.env` file is present and contains a valid OpenAI API key.
- Install all dependencies listed in `requirements.txt`.
- For missing packages, run:
  ```bash
  pip install -r requirements.txt
  ```
- For issues with RSS feeds, check your internet connection and feed URLs.


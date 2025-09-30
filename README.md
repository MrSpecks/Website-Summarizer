# 🔗 Website Scraper & Summarizer

A powerful Streamlit application that scrapes content from any website and generates intelligent summaries using AI. Supports both OpenAI's API and local Ollama endpoints for flexible deployment.

## 📋 Features

- **Smart Web Scraping**: Extracts clean content using BeautifulSoup with intelligent filtering
- **AI-Powered Summarization**: Generates comprehensive summaries using LLMs
- **Flexible LLM Backend**: Choose between OpenAI, OpenRouter, or local Ollama endpoint
- **Dynamic Model Loading**: Automatically fetches available models from API providers
- **Caching**: Built-in caching to prevent re-scraping the same URLs
- **Error Handling**: Robust error handling for network issues, parsing errors, and API failures
- **Modern UI**: Clean, responsive interface with real-time status updates

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (if using OpenAI backend)
- OpenRouter API key (if using OpenRouter backend)
- Ollama installed locally (if using Ollama backend)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Website-Summarizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure secrets** (see Configuration section below)

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## ⚙️ Configuration

### Environment Variables / Secrets

The application uses Streamlit's secrets management. Create a `.streamlit/secrets.toml` file with your configuration:

#### For OpenAI Backend
```toml
OPENAI_API_KEY = "sk-your-openai-api-key-here"
```

#### For OpenRouter Backend
```toml
OPENROUTER_API_KEY = "sk-or-your-openrouter-api-key-here"
```

#### For Ollama Backend
```toml
OLLAMA_ENDPOINT_URL = "http://localhost:11434/v1"
```

#### Example Configuration
See `.streamlit/secrets.toml.example` for a complete template.

### LLM Backend Options

#### OpenAI Backend
- **Models**: gpt-4o-mini (recommended), gpt-4o, gpt-3.5-turbo
- **Setup**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Cost**: Pay-per-use based on token consumption

#### OpenRouter Backend
- **Models**: Access to 200+ models including Claude, Llama, Mistral, and more
- **Setup**: Get API key from [OpenRouter](https://openrouter.ai/keys)
- **Cost**: Pay-per-use with competitive pricing across multiple providers

#### Ollama Backend (Local)
- **Models**: llama2, mistral, codellama, etc.
- **Setup**: Install [Ollama](https://ollama.ai/) and pull a model
- **Cost**: Free (runs locally on your machine)

## 📖 Usage

1. **Enter URL**: Paste the website URL you want to summarize
2. **Select Backend**: Choose OpenAI, OpenRouter, or Ollama from the dropdown
3. **Configure**: Set up your API key or endpoint URL (if not in secrets)
4. **Generate**: Click "Generate Summary" and wait for results
5. **Review**: 
   - Check raw scraped content in the expandable section
   - Read the AI-generated summary in the main area

### Example URLs to Try
- News articles: `https://www.bbc.com/news`
- Documentation: `https://docs.streamlit.io`
- Company websites: `https://openai.com`
- Educational content: `https://www.khanacademy.org`

## 🏗️ Project Structure

```
Website-Summarizer/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── .gitignore                     # Git ignore rules
└── .streamlit/
    ├── secrets.toml.example       # Secrets template
    └── secrets.toml               # Your secrets (not in git)
```

## 🔧 Technical Details

### Core Functions

- **`scrape_and_clean(url)`**: Fetches HTML, parses with BeautifulSoup, removes noise elements
- **`summarize_content(text, title, llm_backend, ...)`**: Calls selected LLM API for summarization
- **Caching**: Uses `@st.cache_data` to cache scraped content for 5 minutes

### Error Handling

- **Network errors**: Connection timeouts, 404 errors, SSL issues
- **Parsing errors**: Malformed HTML, encoding issues
- **API errors**: Invalid keys, model not found, rate limits

### Performance Features

- **Smart caching**: Prevents re-scraping identical URLs
- **Session state**: Preserves user inputs across interactions
- **Loading indicators**: Visual feedback during operations
- **Responsive UI**: Works on desktop and mobile devices

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push your code to GitHub
2. Connect your repository to [Streamlit Cloud](https://share.streamlit.io/)
3. Add your secrets in the Streamlit Cloud dashboard
4. Deploy with one click

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Other Platforms
- **Heroku**: Use the Procfile: `web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
- **Railway**: Deploy directly from GitHub
- **AWS/GCP/Azure**: Use container services

## 🔒 Security Notes

- Never commit your API keys to version control
- Use environment variables or Streamlit secrets for sensitive data
- Consider rate limiting for production deployments
- Validate and sanitize URLs to prevent SSRF attacks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**"OPENAI_API_KEY not found in secrets"**
- Add your API key to `.streamlit/secrets.toml`
- Restart the Streamlit app after adding secrets

**"Connection refused" (Ollama)**
- Ensure Ollama is running: `ollama serve`
- Check the endpoint URL in your configuration
- Verify the model is installed: `ollama list`

**"Parsing error"**
- Some websites use JavaScript to load content
- Try a different URL or check if the site is accessible

**"Network error"**
- Check your internet connection
- Some websites block automated requests
- Try using a different User-Agent header

### Getting Help

- Check the [Streamlit documentation](https://docs.streamlit.io/)
- Review the [OpenAI API documentation](https://platform.openai.com/docs)
- Visit the [Ollama documentation](https://ollama.ai/docs)
- Open an issue in this repository

---

**Made with ❤️ using Streamlit**

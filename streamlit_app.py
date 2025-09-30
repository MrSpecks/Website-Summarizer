import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI, APIError
import time
from typing import Optional, Dict, Any, List

# --- LLM Configuration Mappings ---
# Define supported providers and their API characteristics
LLM_CONFIGS = {
    "OpenAI": {
        "is_remote": True,
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "secret_key_name": "OPENAI_API_KEY",
        "env_key_name": "OPENAI_API_KEY",
    },
    "OpenRouter": {
        "is_remote": True,
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
        "secret_key_name": "OPENROUTER_API_KEY",
        "env_key_name": "OPENROUTER_API_KEY",
    },
    "Ollama (Local)": {
        "is_remote": False,
        "base_url": "http://localhost:11434/v1", # Default endpoint URL for Ollama
        "default_model": "llama2",
    }
}

# --- Session State Initialization ---
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""
if "endpoint_url" not in st.session_state:
    st.session_state["endpoint_url"] = LLM_CONFIGS["Ollama (Local)"]["base_url"]
if "llm_provider" not in st.session_state:
    st.session_state["llm_provider"] = "OpenAI"
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = LLM_CONFIGS["OpenAI"]["default_model"]


# Page configuration
st.set_page_config(
    page_title="Website Scraper & Summarizer",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .summary-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin-top: 1rem;
    }
    .error-container {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .success-container {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# --- Utility Functions ---

def get_api_key(provider: str) -> str:
    """Retrieves the API key from session state, then secrets, then environment."""
    
    # 1. Check user-input key in session state (highest priority for demo)
    if st.session_state.get("api_key"):
        return st.session_state["api_key"]

    config = LLM_CONFIGS.get(provider, {})
    secret_key = config.get("secret_key_name", "")
    env_key = config.get("env_key_name", "")

    # 2. Check Streamlit secrets
    key = st.secrets.get(secret_key)
    if key:
        return key

    # 3. Check environment variables
    key = os.getenv(env_key)
    if key:
        return key

    # If no key found, raise a user-friendly error
    raise RuntimeError(
        f"API key not found. Please enter your {provider} key in the sidebar."
    )

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_available_models(provider: str, api_key: str) -> List[str]:
    """Fetches the list of available models for a given provider/key from API."""
    if provider not in LLM_CONFIGS or not LLM_CONFIGS[provider]["is_remote"]:
        return []

    config = LLM_CONFIGS[provider]
    base_url = config['base_url']
    
    try:
        # Use the OpenAI client to query the /models endpoint
        client = OpenAI(api_key=api_key, base_url=base_url)
        models_response = client.models.list()
        
        model_names = [m.id for m in models_response.data]
        
        # Simple sorting and return
        return sorted(model_names)
        
    except APIError as e:
        # Catch authentication/rate limit errors
        st.warning(f"Could not fetch models for {provider}. Check API key validity. Error Code: {e.status_code}")
        return []
    except Exception as e:
        st.warning(f"An unexpected error occurred while fetching models: {e}")
        return []

# Caching decorator removed to resolve UnserializableReturnValueError
def scrape_and_clean(url: str) -> Dict[str, Any]:
    """
    Scrape and clean website content using BeautifulSoup.
    Returns a dictionary with title, text, and metadata.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract title
        title = soup.title.string if soup.title else "No title found"
        
        # Remove irrelevant elements
        for element in soup(["script", "style", "img", "input", "nav", "footer", "header"]):
            element.decompose()
        
        # Get clean text
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up excessive whitespace
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
        
        return {
            "title": title,
            "text": text,
            "url": url,
            "status": "success"
        }
        
    except requests.exceptions.RequestException as e:
        # Explicitly cast exception message to string to prevent Streamlit cache errors (though caching is now disabled)
        error_msg = str(e)
        return {
            "title": None,
            "text": None,
            "url": url,
            "status": "error",
            "error": f"Network error: {error_msg}"
        }
    except Exception as e:
        # Explicitly cast exception message to string to prevent Streamlit cache errors (though caching is now disabled)
        error_msg = str(e)
        return {
            "title": None,
            "text": None,
            "url": url,
            "status": "error",
            "error": f"Parsing error: {error_msg}"
        }


def summarize_content(text: str, title: str, provider: str, model_name: str) -> str:
    """
    Generate summary using the selected LLM backend, model, and configuration.
    """
    
    # 1. Determine API client configuration
    config = LLM_CONFIGS.get(provider)
    if not config:
        raise ValueError(f"Unsupported provider: {provider}")

    base_url = config.get("base_url")
    api_key = None
    
    if config["is_remote"]:
        api_key = get_api_key(provider) # Will raise RuntimeError if key is missing
        
        # If the user selected Ollama as a remote provider but failed to set a URL, 
        # we still need to set the base_url for the client, so we use the session state URL.
        client = OpenAI(api_key=api_key, base_url=base_url)
    
    else: # Ollama (Local)
        base_url = st.session_state["endpoint_url"]
        # Ollama typically ignores the API key, but the client requires a non-None value
        client = OpenAI(base_url=base_url, api_key="ollama_local_key") 
    
    # 2. Build prompts
    system_prompt = (
        "You are an assistant that analyzes the contents of a website or web application "
        "and provides a comprehensive summary of the website's content, ignoring navigation "
        "elements and focusing on the main information. Respond in markdown format with "
        "clear headings and bullet points."
    )
    
    user_prompt = (
        f"You are looking at a website titled '{title}'\n\n"
        "The contents of this website are as follows; please provide a detailed summary "
        "of this website in markdown. If it includes news or announcements, then "
        "summarize these too. Focus on the main content and key information.\n\n"
        f"{text}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # 3. Call API
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=1000
    )
    
    return response.choices[0].message.content


# -----------------------------
# UI Component Functions
# -----------------------------

def llm_config_selector():
    st.subheader("🤖 LLM Backend Setup")
    
    # 1. Provider Selection
    provider = st.selectbox(
        "Select LLM Provider:",
        options=list(LLM_CONFIGS.keys()),
        key="llm_provider",
        help="Choose between OpenAI, OpenRouter, or a local Ollama endpoint."
    )
    
    config = LLM_CONFIGS[provider]
    
    if config["is_remote"]:
        # 2a. Remote Provider Key Input (OpenAI/OpenRouter)
        st.text_input(
            f"Paste your {provider} API Key here:",
            type="password",
            key="api_key",
            help=f"Your key is only stored in the current browser session and is never saved. Reads from {config['secret_key_name']} in secrets.toml if empty."
        )

        try:
            current_key = get_api_key(provider)
            st.info(f"Key Status: **✅ Key Loaded** (via session or secrets)")
            
            # 3a. Dynamic Model Loading for Remote Providers
            with st.spinner(f"Fetching models from {provider}..."):
                model_options = fetch_available_models(provider, current_key)

            if not model_options:
                model_options = [config["default_model"], "--- Could not load models ---"]
                
            st.selectbox(
                "Select Model:",
                options=model_options,
                key="selected_model",
                index=0,
                help="The list is dynamically loaded from the API. Choose a powerful chat model."
            )
        except RuntimeError:
            st.error("Key Status: ❌ Key Missing")
            st.session_state["selected_model"] = config["default_model"]
            st.selectbox(
                "Select Model:",
                options=[config["default_model"], "--- Please load key first ---"],
                key="selected_model",
                index=0,
                disabled=True
            )
            
    else: # Ollama (Local Endpoint)
        # 2b. Ollama Endpoint URL Input
        st.text_input(
            "Ollama Endpoint URL",
            value=config["base_url"],
            key="endpoint_url",
            help="The URL for your local Ollama server (e.g., http://localhost:11434/v1)"
        )
        
        # 3b. Static Model Name Input for Ollama
        st.text_input(
            "Model Name (in Ollama)",
            value=config["default_model"],
            key="selected_model",
            help="Enter the exact name of the model installed in Ollama (e.g., llama2, mistral)"
        )
        st.info("Ollama does not require an external API key.")


def main():
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🔗 Website Scraper & Summarizer")
    st.markdown("Extract and summarize content from any website using AI")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # LLM Configuration
        llm_config_selector()
        
        st.markdown("---")
        
        # URL input
        url = st.text_input(
            "Target Website URL",
            value=st.session_state.get("url", "https://streamlit.io/"),
            placeholder="https://example.com",
            help="Enter the URL of the website you want to summarize"
        )
        
        # Store URL in session state
        st.session_state.url = url
        
        # Generate button
        generate_summary = st.button(
            "🚀 Generate Summary",
            type="primary",
            use_container_width=True
        )
    
    # --- Main content area ---
    
    if generate_summary and url:
        # Validate URL
        if not url.startswith(("http://", "https://")):
            st.error("❌ Please enter a valid URL starting with http:// or https://")
            return
        
        # Check LLM configuration validity before starting the scrape
        provider = st.session_state["llm_provider"]
        model_name = st.session_state["selected_model"]
        
        if LLM_CONFIGS[provider]["is_remote"]:
            try:
                get_api_key(provider) # Check if key is available
            except RuntimeError as e:
                st.markdown(f'<div class="error-container">❌ **LLM Configuration Error:** {str(e)}</div>', unsafe_allow_html=True)
                return

        # 1. Scraping phase
        st.subheader("📥 Scraping Website Content")
        with st.spinner(f"Scraping content from {url}..."):
            # Removed caching call here
            scraped_data = scrape_and_clean(url)
        
        if scraped_data["status"] == "error":
            st.markdown(f'<div class="error-container">❌ **Scraping Failed:** {scraped_data["error"]}</div>', unsafe_allow_html=True)
            return
        
        st.markdown(f'<div class="success-container">✅ **Successfully scraped:** {scraped_data["title"]}</div>', unsafe_allow_html=True)
        
        # Display raw content in expander
        with st.expander("📄 Raw Scraped Content", expanded=False):
            st.text_area(
                "Cleaned text content",
                value=scraped_data["text"],
                height=300,
                disabled=True
            )
        
        # 2. Summarization phase
        st.subheader("🤖 AI Summary Generation")
        
        with st.spinner(f"Generating summary using **{provider}** and model **{model_name}**..."):
            try:
                summary = summarize_content(
                    text=scraped_data["text"],
                    title=scraped_data["title"],
                    provider=provider,
                    model_name=model_name
                )
                
                # Display summary
                st.markdown('<div class="summary-container">', unsafe_allow_html=True)
                st.markdown("## 📋 AI-Generated Summary")
                st.markdown(summary)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.markdown(f'<div class="error-container">❌ **Error generating summary:** {str(e)}</div>', unsafe_allow_html=True)

    elif generate_summary and not url:
        st.warning("⚠️ Please enter a URL to summarize")
    
    # Instructions when no action taken
    if not generate_summary:
        st.info("👈 Configure your settings in the sidebar and click 'Generate Summary' to get started!")
        
        # Example usage
        with st.expander("📖 How to use this app"):
            st.markdown("""
            ### Quick Start Guide
            
            1. **Enter URL**: Paste the website URL you want to summarize.
            2. **Choose Provider**: Select OpenAI, OpenRouter, or Ollama (local).
            3. **Configure Key/Model**: 
               * For OpenAI/OpenRouter, paste your API key (or use a key from `secrets.toml`). The model list is dynamically loaded.
               * For Ollama, confirm the local endpoint and model name.
            4. **Generate**: Click the "🚀 Generate Summary" button.
            
            ### About Providers
            
            **OpenAI / OpenRouter:** Use a unified API client to access various powerful models. Ensure your key is valid to dynamically load the model list.
            
            **Ollama (Local):** This option uses your local machine's computing power and runs models entirely locally, keeping data completely private. Ensure Ollama is running and the model you specify is downloaded.
            """)


if __name__ == "__main__":
    main()

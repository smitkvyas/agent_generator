from langchain_groq import ChatGroq


def load_llm(model: str = None, temperature: float = None, request_timeout: int = None, max_retries: int = None):
    return ChatOpenAI(
        model=model if model else "gpt-4-turbo",
        temperature=temperature if temperature else 0.2,
        request_timeout=request_timeout if request_timeout else 60,
        max_retries=max_retries if max_retries else 3
    )


def load_llm_groq(model: str = None, temperature: float = None, request_timeout: int = None, max_retries: int = None):
    return ChatGroq(
        model=model if model else "llama-3.3-70b-versatile",
        temperature=temperature if temperature else 0.2,
        request_timeout=request_timeout if request_timeout else 60,
        max_retries=max_retries if max_retries else 3
    )

def load_llm_gemini(model: str = None, temperature: float = None, request_timeout: int = None, max_retries: int = None):
    return ChatGoogleGenerativeAI(
        model=model if model else "gemini-3.1-flash-lite",
        temperature=temperature if temperature else 0.2,
        request_timeout=request_timeout if request_timeout else 60,
        max_retries=max_retries if max_retries else 3
    )
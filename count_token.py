import tiktoken

def count_and_show_tokens(text: str, model_name: str = "gpt-4"):
    # Load the correct tokenizer
    encoding = tiktoken.encoding_for_model(model_name)
    
    # Convert text to token IDs
    token_ids = encoding.encode(text)
    
    # Convert token IDs back to text pieces
    token_strings = [encoding.decode([tid]) for tid in token_ids]
    
    print(f"--- Analysis for {model_name} ---")
    print(f"Original Text: \"{text}\"")
    print(f"Total Tokens:  {len(token_ids)}")
    print(f"Token Pieces:  {token_strings}\n")

# Try out a few examples!
count_and_show_tokens("Tokenization is unforgettable!")
count_and_show_tokens("Hello world")

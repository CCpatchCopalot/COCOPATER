import os
import json
import openai
import time
from bs4 import BeautifulSoup
from openai.error import APIError, Timeout, APIConnectionError

# Configure OpenAI-compatible Ark endpoint
openai.api_key = "d9e5c465-c0f2-45fb-8737-ea04644a4273"
openai.api_base = "https://ark.cn-beijing.volces.com/api/v3"
# Add timeout settings
openai.timeout = 30  # seconds
openai.api_version = None  # Make sure no API version is set for compatibility

def process_poc(poc_dir):
    html_path = os.path.join(poc_dir, "poc.html")
    if not os.path.exists(html_path):
        print(f"No poc.html in {poc_dir}, skipping")
        return
        
    # Read and parse HTML using BeautifulSoup
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    # Extract text content and remove extra whitespace
    html_content = ' '.join(soup.get_text().split())
    print(f"Processed HTML content length: {len(html_content)}")
    
    system_prompt = (
        "You are an assistant that generates a proof-of-concept exploit code and a README with reproduction steps "
        "based on the provided HTML proof-of-concept. Please output a JSON object with two keys: \"poc_code\" and "
        "\"readme\". \"poc_code\" should contain the Python exploit file content. \"readme\" should contain the README.md "
        "content in English with sections: POC URL, Compilation Environment, Run Command, and Expected Output."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": html_content},
    ]
    
    # Use streaming for the completion with error handling
    max_retries = 3
    retry_delay = 5
    full_content = ""
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} - Generating response...")
            
            # Create completion with timeout
            stream = openai.ChatCompletion.create(
                model="deepseek-r1-250528",
                messages=messages,
                stream=True,
                request_timeout=30,  # Add request timeout
            )
            
            # Process the stream
            for chunk in stream:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content_chunk = chunk.choices[0].delta.content
                    if content_chunk:
                        print(content_chunk, end='', flush=True)
                        full_content += content_chunk
            
            print("\nResponse generation completed.")
            break  # If successful, break the retry loop
            
        except (APIError, Timeout, APIConnectionError) as e:
            print(f"\nAPI Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Skipping this POC.")
                return
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            return
    
    if not full_content:
        print("No content generated. Skipping this POC.")
        return
    
    try:
        result = json.loads(full_content)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON for {poc_dir}, content: {full_content}")
        return
        
    poc_file_path = os.path.join(poc_dir, "poc")
    with open(poc_file_path, "w", encoding="utf-8") as f:
        f.write(result.get("poc_code", ""))
        
    readme_file_path = os.path.join(poc_dir, "README.md")
    with open(readme_file_path, "w", encoding="utf-8") as f:
        f.write(result.get("readme", ""))

if __name__ == "__main__":
    pocs_root = os.path.join(os.getcwd(), "pocs")
    for entry in os.listdir(pocs_root):
        poc_dir = os.path.join(pocs_root, entry)
        if os.path.isdir(poc_dir):
            print(f"Processing {entry}...")
            process_poc(poc_dir)
    print("Done.")
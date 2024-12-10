import requests
from newspaper import Article
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

# Function to perform a DuckDuckGo search using the ddg API
def search_articles_duckduckgo(query, num_results=10):
    try:
        response = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(response.content, "html.parser")
        results = []
        for link in soup.find_all("a", {"class": "result__a"}, limit=num_results):
            url = link["href"]
            original_url = unwrap_duckduckgo_url(url)
            if original_url:
                results.append(original_url)
        return results
    except Exception as e:
        print(f"Error during search: {e}")
        return []

# Function to unwrap DuckDuckGo redirect URLs
def unwrap_duckduckgo_url(wrapped_url):
    try:
        parsed_url = urlparse(wrapped_url)
        query_params = parse_qs(parsed_url.query)
        if "uddg" in query_params:
            return unquote(query_params["uddg"][0])
        return wrapped_url
    except Exception as e:
        print(f"Error unwrapping URL: {e}")
        return None

# Function to extract content from an article
def extract_article_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return None

# Function to search and process articles relevant to a claim
def search_and_process_articles(claim, num_results=10):
    print(f"Searching for articles relevant to the claim: {claim}")
    urls = search_articles_duckduckgo(claim, num_results)
    
    data = []
    for url in urls:
        print(f"Processing: {url}")
        content = extract_article_content(url)
        if content:
            data.append({
                "claim": claim,
                "url": url,
                "content": content
            })
    return pd.DataFrame(data)

# Example usage
def test():
    # Define the claim
    claim = "MicroStrategy has benefited from the rally in cryptocurrencies this year"

    # Fetch and process articles relevant to the claim
    num_results = 5
    dataset = search_and_process_articles(claim, num_results)

    # Print the first two rows without shortening
    # pd.set_option("display.max_colwidth", None)  # Ensures all column content is shown
    print(dataset.head())

    # Save the dataset for analysis
    dataset.to_csv('relevant_articles_dataset.csv', index=False)
    print(f"Dataset saved as 'relevant_articles_dataset.csv'. Contains {len(dataset)} articles.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Get relevant infomation from website for a Claim")
    parser.add_argument(
        "--claim", 
        type=str, 
        required=True, 
        help="The claim to verify."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="File to save the verification result (default: verification_result.csv)"
    )
    parser.add_argument(
        "--num_results", 
        type=int, 
        default=5, 
        help="Number of articles to retrieve for context (default: 5)."
    )
    
    args = parser.parse_args()
    
    # Process the claim
    result = search_and_process_articles(args.claim, args.num_results)
    
    # Save result to a file
    if args.output:
        result.to_csv(args.output, index=False)
        print(f"Verification result saved to '{args.output}'.")

    print(result.head())
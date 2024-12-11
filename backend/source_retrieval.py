import requests
from newspaper import Article
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

import argparse
import json
from pathlib import Path
import google.generativeai as genai

@dataclass
class ArticleInfo:
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    date: Optional[datetime] = None
    authors: Optional[List[str]] = None
    source: Optional[str] = None
    claim: Optional[str] = None

class SourceRetriever:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
        
    def search_articles_duckduckgo(self, query: str, num_results: int = 10) -> List[str]:
        """Search for articles using DuckDuckGo."""
        try:
            response = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                headers=self.headers
            )
            soup = BeautifulSoup(response.content, "html.parser")
            results = []
            for link in soup.find_all("a", {"class": "result__a"}, limit=num_results):
                url = link["href"]
                original_url = self._unwrap_duckduckgo_url(url)
                if original_url:
                    results.append(original_url)
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def _unwrap_duckduckgo_url(self, wrapped_url: str) -> Optional[str]:
        """Unwrap DuckDuckGo redirect URLs."""
        try:
            parsed_url = urlparse(wrapped_url)
            query_params = parse_qs(parsed_url.query)
            if "uddg" in query_params:
                return unquote(query_params["uddg"][0])
            return wrapped_url
        except Exception as e:
            print(f"Error unwrapping URL: {e}")
            return None

    def extract_article_info(self, url: str, claim: Optional[str] = None) -> Optional[ArticleInfo]:
        """Extract information from an article."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return ArticleInfo(
                url=url,
                title=article.title,
                content=article.text,
                date=article.publish_date,
                authors=article.authors,
                source=urlparse(url).netloc,
                claim=claim
            )
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None

    def verify_claim_with_gemini(self, claim: str, context: str) -> Optional[Dict[str, Any]]:
        """Verify a claim using Gemini API with provided context."""
        if not self.model:
            print("Gemini API key not configured")
            return None

        try:
            prompt = f"""
            You must respond with valid JSON only. Analyze this claim using the provided context:
            
            Claim: {claim}
            
            Context:
            {context}
            
            Respond with this exact JSON structure, no other text:
            {{
                "claim": "{claim}",
                "verdict": "<TRUE/FALSE/PARTIALLY TRUE/INSUFFICIENT EVIDENCE>",
                "confidence": "<HIGH/MEDIUM/LOW>",
                "explanation": "<your explanation>",
                "supporting_evidence": ["<evidence1>", "<evidence2>"],
                "contrary_evidence": ["<evidence1>", "<evidence2>"],
                "limitations": ["<limitation1>", "<limitation2>"]
            }}
            """

            response = self.model.generate_content(prompt)
            
            # Store raw response
            raw_response = response.text if response.parts else "No response generated"
            
            # Try to parse JSON response
            if response.parts:
                try:
                    result = json.loads(response.text)
                    return result, raw_response
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON. Raw response: {raw_response}")
                    return None, raw_response
            return None, raw_response

        except Exception as e:
            print(f"Error during claim verification: {e}")
            return None, str(e)

    def search_and_process_articles(self, claim: str, num_results: int = 10, verify: bool = False) -> pd.DataFrame:
        """Search and process articles relevant to a claim, optionally verify with Gemini."""
        print(f"Searching for articles relevant to the claim: {claim}")
        urls = self.search_articles_duckduckgo(claim, num_results)
        
        data = []
        context = ""
        for url in urls:
            print(f"Processing: {url}")
            article_info = self.extract_article_info(url, claim)
            if article_info:
                data.append(article_info.__dict__)
                if verify and article_info.content:
                    context += article_info.content + "\n\n"
        
        results_df = pd.DataFrame(data)
        
        if verify and self.model:
            verification_result, raw_response = self.verify_claim_with_gemini(claim, context)
            if verification_result:
                print("\nClaim Verification Result:")
                print(json.dumps(verification_result, indent=2))
                results_df.attrs['verification'] = verification_result
            results_df.attrs['raw_gemini_response'] = raw_response
        
        return results_df


def save_results(df: pd.DataFrame, output_path: str):
    """Save results to a file based on extension."""
    path = Path(output_path)
    if path.suffix == '.csv':
        df.to_csv(path, index=False)
    elif path.suffix == '.json':
        df.to_json(path, orient='records', date_format='iso')
    else:
        raise ValueError("Output file must be either .csv or .json")

def main():
    """Command line interface for source retrieval."""
    parser = argparse.ArgumentParser(description='Search and process articles for fact-checking.')
    parser.add_argument('claim', help='The claim to verify')
    parser.add_argument('-n', '--num-results', type=int, default=5,
                      help='Number of articles to retrieve (default: 5)')
    parser.add_argument('-o', '--output', help='Output file path (.csv or .json)')
    parser.add_argument('--verbose', action='store_true',
                      help='Print detailed processing information')
    parser.add_argument('--gemini-key', help='Gemini API key for claim verification')
    parser.add_argument('--verify', action='store_true',
                      help='Verify claim using Gemini API')

    args = parser.parse_args()
    
    retriever = SourceRetriever(gemini_api_key=args.gemini_key if args.verify else None)
    results_df = retriever.search_and_process_articles(
        args.claim, 
        args.num_results,
        verify=args.verify
    )
    
    if args.verbose:
        print("\nResults found:")
        for idx, row in results_df.iterrows():
            print(f"\nSource {idx + 1}:")
            print(f"Title: {row['title']}")
            print(f"URL: {row['url']}")
            print(f"Date: {row['date']}")
            print(f"Source: {row['source']}")
            if row['authors']:
                print(f"Authors: {', '.join(row['authors'])}")
            print("-" * 50)

    if args.output:
        save_results(results_df, args.output)
        print(f"\nResults saved to: {args.output}")
    else:
        # Print a simple summary if no output file specified
        print("\nSummary:")
        for idx, row in results_df.iterrows():
            print(f"{idx + 1}. {row['title']} ({row['source']})")

    if args.verify and 'verification' in results_df.attrs:
        print("\nVerification Result:")
        print(json.dumps(results_df.attrs['verification'], indent=2))

if __name__ == "__main__":
    main()
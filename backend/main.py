def process_claim(claim, gemini_api_key, num_results=5):
    print(f"Processing claim: {claim}")
    
    # Search for relevant articles
    urls = search_articles_duckduckgo(claim, num_results)
    print(f"Found {len(urls)} articles.")
    
    # Extract content from articles
    context = ""
    for url in urls:
        print(f"Fetching content from: {url}")
        content = extract_article_content(url)
        if content:
            context += content + "\n\n"
    
    # Verify claim with Gemini API
    print("Verifying claim with Gemini API...")
    result = verify_claim_with_gemini(claim, context, gemini_api_key)
    
    if result:
        print("Claim Verification Result:")
        print(result)
        return result
    else:
        print("Failed to verify claim.")
        return None

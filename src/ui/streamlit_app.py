import streamlit as st
from src.core.source_retrieval import SourceRetriever
import pandas as pd

class SourceRetrieverUI:
    def __init__(self):
        self.retriever = None  # Initialize later with API key if provided

    def render_article_info(self, idx: int, row: pd.Series):
        """Render article information in the Streamlit UI."""
        def escape_markdown(text):
            """Escape markdown special characters."""
            if not isinstance(text, str):
                return text
            # Characters to escape: * _ ` [ ] ( ) # + - . ! { } > |
            special_chars = ['$', '*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!', '{', '}', '>', '|']
            for char in special_chars:
                text = text.replace(char, '\\' + char)
            return text

        title = escape_markdown(row['title'] if row['title'] else row['url'][:100])
        with st.expander(f"Source {idx + 1}: {title}..."):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Source Website:**")
                st.write(escape_markdown(row['source']))
                st.write("**URL:**")
                st.markdown(row['url'])  # Don't escape URLs
                
            with col2:
                st.write("**Publication Date:**")
                st.write(row['date'].strftime('%Y-%m-%d') if pd.notnull(row['date']) else 'Date not available')
                if row['authors']:
                    st.write("**Authors:**")
                    st.write(escape_markdown(", ".join(row['authors'])))
            
            st.write("**Content:**")
            st.write(escape_markdown(row['content']))

    def render_search_results(self, results_df: pd.DataFrame):
        """Render search results in the Streamlit UI."""
        st.header("Search Results")
        if not results_df.empty:
            for idx, row in results_df.iterrows():
                self.render_article_info(idx, row)
            
            # Add download button for CSV
            st.download_button(
                label="Download results as CSV",
                data=results_df.to_csv(index=False).encode('utf-8'),
                file_name='search_results.csv',
                mime='text/csv',
            )
        else:
            st.warning("No results found.")

    def render_verification_result(self, verification_result, raw_response=None):
        """Render verification results in the Streamlit UI."""
        st.header("Claim Verification Result")
        
        # Show raw response in expander if available
        if raw_response:
            with st.expander("Show Raw Gemini Response"):
                st.text(raw_response)
        
        if verification_result:
            # Determine the color based on the verdict
            verdict_color = {
                "TRUE": "darkgreen",
                "FALSE": "darkred",
                "PARTIALLY TRUE": "#FFB80F",
                "INSUFFICIENT EVIDENCE": "#FFB80F"
            }.get(verification_result['verdict'], "black")  # Default to black if not found

            # Display the verdict with color
            st.markdown(f"<h3 style='color: {verdict_color};'>Verdict: {verification_result['verdict']}</h3>", unsafe_allow_html=True)
            st.write(f"**Confidence:** {verification_result['confidence']}")
            st.write("**Explanation:**")
            st.write(verification_result['explanation'])
            
            st.write("**Supporting Evidence:**")
            for evidence in verification_result['supporting_evidence']:
                st.write(f"- {evidence}")
            
            st.write("**Contrary Evidence:**")
            for evidence in verification_result['contrary_evidence']:
                st.write(f"- {evidence}")
        else:
            st.error("Could not parse Gemini response into the expected format")

    def main(self):
        """Main UI rendering function."""
        st.title("Source Retrieval System")
        
        # API Key input in sidebar
        with st.sidebar:
            api_key = st.text_input("Enter Gemini API Key (optional):", type="password")
            verify_enabled = st.checkbox("Enable claim verification", 
                                      disabled=not bool(api_key))

        # Initialize retriever with API key if provided
        self.retriever = SourceRetriever(gemini_api_key=api_key if verify_enabled else None)
        
        # Input section
        st.header("Enter Your Claim")
        claim = st.text_area("Enter the claim you want to verify:", height=100)
        num_results = st.slider("Number of articles to retrieve:", 
                              min_value=1, max_value=20, value=5)
        
        # Search button
        if st.button("Search for Sources") and claim:
            with st.spinner('Searching and analyzing...'):
                try:
                    results_df = self.retriever.search_and_process_articles(
                        claim, num_results, verify=verify_enabled
                    )
                    self.render_search_results(results_df)
                    
                    # Display verification results if available
                    if verify_enabled:
                        raw_response = results_df.attrs.get('raw_gemini_response')
                        verification_result = results_df.attrs.get('verification')
                        self.render_verification_result(verification_result, raw_response)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    app = SourceRetrieverUI()
    app.main()
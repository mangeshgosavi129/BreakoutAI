import streamlit as st
import pandas as pd
from typing import Optional
from helper import (
    csv_to_dataframe,
    sheets_to_dataframe,
    dataframe_to_sheets,
    seo_query_optimizer,
    get_search_results,
    extract_exact_info_from_results
)
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def init_session_state():
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

def load_data(file_source: str) -> Optional[pd.DataFrame]:
    df = None
    
    if file_source == "Upload CSV":
        uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
        if uploaded_file:
            try:
                df = csv_to_dataframe(uploaded_file)
                st.success("CSV file loaded successfully!")
            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")
    
    elif file_source == "Google Sheets":
        sheet_url = st.text_input("Enter Google Sheets URL")
        if sheet_url:
            try:
                credentials_path = os.getenv("CREDENTIALS_PATH")
                df = sheets_to_dataframe(sheet_url, credentials_path)
                st.success("Google Sheet loaded successfully!")
            except Exception as e:
                st.error(f"Error loading Google Sheet: {str(e)}")
    
    return df

def process_data(df: pd.DataFrame, name_column: str, query_template: str) -> None:
    """Process each row in the dataframe and update the 'response' column with results."""
    # Ensure the 'response' column exists in the DataFrame
    if 'response' not in df.columns:
        df['response'] = None

    # Optimize query once before the loop
    optimized_query_template = seo_query_optimizer(query_template)
    
    # Initialize Streamlit progress components
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, row in df.iterrows():
        try:
            # Update progress
            progress = (idx + 1) / len(df)
            progress_bar.progress(progress)
            status_text.text(f"Processing {idx + 1} of {len(df)}: {row[name_column]}")
            
            # Skip if name is empty
            if pd.isna(row[name_column]):
                df.at[idx, 'response'] = "Empty name provided"
                continue
            
            # Substitute the name in the pre-optimized query
            current_query = optimized_query_template.replace("{Name}", str(row[name_column]))
            
            # Get and process search results
            search_results = get_search_results(current_query)
            extracted_info = extract_exact_info_from_results(search_results, current_query)
            
            # Store results directly in the DataFrame's 'response' column
            df.at[idx, 'response'] = extracted_info if extracted_info else "No information found"
            
        except Exception as e:
            df.at[idx, 'response'] = f"Error: {str(e)}"
    
    st.session_state.processing_complete = True

def save_results(output_format: str, results_df: pd.DataFrame):
    if output_format == "CSV":
        csv_data = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results CSV",
            data=csv_data,
            file_name="search_results.csv",
            mime="text/csv"
        )
    
    elif output_format == "Google Sheets":
        sheet_url = st.text_input("Enter destination Google Sheet URL")
        if sheet_url and st.button("Save to Google Sheets"):
            try:
                credentials_path = os.getenv("CREDENTIALS_PATH")
                dataframe_to_sheets(results_df, sheet_url, credentials_path)
                st.success("Results saved to Google Sheets successfully!")
            except Exception as e:
                st.error(f"Error saving to Google Sheets: {str(e)}")

def main():
    st.set_page_config(page_title="BreakoutAI", layout="wide")
    st.title("BreakoutAI")
    st.markdown("---")
    
    init_session_state()
    
    with st.expander("Data Input Settings", expanded=True):
        file_source = st.radio("Choose data source:", ["Upload CSV", "Google Sheets"])
        df = load_data(file_source)
        
        if df is not None:
            st.write("Preview of loaded data:")
            st.dataframe(df.head())
            
            name_column = st.selectbox("Select name column:", df.columns.tolist())
            query_template = st.text_input(
                "Customize search query:",
                value="find email address for {Name}",
                help="Use {Name} as a placeholder for the name"
            )
            
            if st.button("🔍 Start Processing"):
                st.session_state.results = []  # Reset results
                st.session_state.processing_complete = False
                process_data(df, name_column, query_template)
    
    if st.session_state.processing_complete:
        st.markdown("### Results")
        results_df = pd.DataFrame(st.session_state.results)
        st.dataframe(results_df)
        
        # Save options
        output_format = st.radio("Save results as:", ["CSV", "Google Sheets"])
        save_results(output_format, results_df)
    
    # Footer
    st.markdown("---")
    st.markdown("Created with ❤️ | [Documentation](https://your-docs-link.com)")

if __name__ == "__main__":
    main()
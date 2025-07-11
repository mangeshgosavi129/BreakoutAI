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
def init_session_state():
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

def load_data(file_source: str, credentials_path: str) -> Optional[pd.DataFrame]:
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
                df = sheets_to_dataframe(sheet_url, credentials_path)
                st.success("Google Sheet loaded successfully!")
            except Exception as e:
                st.error(f"Error loading Google Sheet: {str(e)}")
    
    return df

def process_data(df: pd.DataFrame, name_column: str, query_template: str, serp_api_key: str, together_api_key: str) -> pd.DataFrame:
    """Process each row in the dataframe and update the 'Responses' column with results."""
    if 'Responses' not in df.columns:
        df['Responses'] = None

    optimized_query_template = seo_query_optimizer(query_template, together_api_key)
    if not optimized_query_template:
        st.error("Failed to optimize query. Please check your Together API key.")
        return df

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, row in df.iterrows():
        try:
            progress = (idx + 1) / len(df)
            progress_bar.progress(progress)
            status_text.text(f"Processing {idx + 1} of {len(df)}: {row[name_column]}")
            
            if pd.isna(row[name_column]):
                df.at[idx, 'Responses'] = "Empty name provided"
                continue
            
            current_query = optimized_query_template.replace("{Name}", str(row[name_column]))
            
            search_results = get_search_results(current_query, serp_api_key)
            extracted_info = extract_exact_info_from_results(search_results, current_query, together_api_key)
            
            df.at[idx, 'Responses'] = extracted_info if extracted_info else "No information found"
            
        except Exception as e:
            df.at[idx, 'Responses'] = f"Error: {str(e)}"
    
    st.session_state.processing_complete = True
    return df

def save_results(output_format: str, results_df: pd.DataFrame, credentials_path: str):
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
                dataframe_to_sheets(results_df, sheet_url, credentials_path)
                st.success("Results saved to Google Sheets successfully!")
            except Exception as e:
                st.error(f"Error saving to Google Sheets: {str(e)}")

def main():
    st.set_page_config(page_title="BreakoutAI", layout="wide")
    
    st.sidebar.title("API Configuration")
    serp_api_key = st.sidebar.text_input("SERP API Key", type="password")
    together_api_key = st.sidebar.text_input("Together API Key", type="password")
    credentials_path = st.sidebar.text_input("Google Credentials Path", help="Path to your Google credentials JSON file.")

    st.title("BreakoutAI")
    st.markdown("---")
    
    init_session_state()
    
    with st.expander("Data Input Settings", expanded=True):
        file_source = st.radio("Choose data source:", ["Upload CSV", "Google Sheets"])
        df = load_data(file_source, credentials_path)
        
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
                if not all([serp_api_key, together_api_key, credentials_path]):
                    st.error("Please provide all API keys and credentials path in the sidebar.")
                else:
                    st.session_state.processing_complete = False
                    st.session_state.results_df = process_data(df, name_column, query_template, serp_api_key, together_api_key)
                    st.session_state.processing_complete = True
    
    if st.session_state.processing_complete:
        results_df = st.session_state.get("results_df", pd.DataFrame())
        st.markdown("### Results")
        st.dataframe(results_df)
        
        output_format = st.radio("Save results as:", ["CSV", "Google Sheets"])
        save_results(output_format, results_df, credentials_path)
    
    st.markdown("---")
    st.markdown("Created with ❤️ | [Documentation](https://docs.google.com/document/d/1nu1fckgzr8YSaywodM_2OCMyvjE981LZHMl-o6EGo3U/edit?usp=sharing)")

if __name__ == "__main__":
    main()

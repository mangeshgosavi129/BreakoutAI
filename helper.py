import pandas as pd
import gspread
from google.oauth2 import service_account
import re,os
from dotenv import load_dotenv
from together import Together
from serpapi import GoogleSearch

load_dotenv()


def csv_to_dataframe(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        df['Responses']=''
        return df
    except Exception as e:
        raise Exception(f"Error reading CSV file: {str(e)}")

def sheets_to_dataframe(sheet_url: str, credentials_path: str) -> pd.DataFrame:
    try:
        # Initialize Google Sheets client
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        client = gspread.authorize(credentials)

        # Extract sheet ID from URL
        sheet_id = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url).group(1)
        
        # Get sheet data
        sheet = client.open_by_key(sheet_id).sheet1
        data = sheet.get_all_records()
        
        df = pd.DataFrame(data)
        df['Responses']=''
        return df

    except Exception as e:
        raise Exception(f"Error reading Google Sheet: {str(e)}")

def dataframe_to_csv(df: pd.DataFrame, output_path: str) -> None:
    try:
        df.to_csv(output_path, index=False)
    except Exception as e:
        raise Exception(f"Error saving to CSV: {str(e)}")

def dataframe_to_sheets(df: pd.DataFrame, sheet_url: str, credentials_path: str) -> None:
    try:
        # Initialize Google Sheets client
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(credentials)

        # Extract sheet ID from URL
        sheet_id = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url).group(1)
        
        # Get worksheet and clear it
        worksheet = client.open_by_key(sheet_id).sheet1
        worksheet.clear()

        # Update with new data
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    except Exception as e:
        raise Exception(f"Error updating Google Sheet: {str(e)}")

def seo_query_optimizer(input_query: str, together_api_key: str) -> str:
    try:
        client = Together(api_key=together_api_key)
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            messages=[{
                "role": "user",
                "content": f"Provide only the single, primary SEO-optimized query text for this input: '{input_query}', respond with no extra text, explanations, or formatting, just the exact query text and if there are curly brackets, keep them as it representes a placeholder"
            }],
        )
        seo_optimized_content = completion.choices[0].message.content
        return seo_optimized_content
    
    except Exception as e:
        print("Error during SEO optimization:", e)
        return None

def get_search_results(query: str, serp_api_key: str) -> dict:
    params = {
        "q": query,  # Your search query
        "api_key": serp_api_key,  # Your SerpAPI key
        "engine": "google",  # We are using Google search engine here
        "google_domain": "google.com",  # Set the domain for Google search
        "gl": "in",  # Country-specific results (optional)
        "hl": "en",  # Language (optional)
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    return results

def extract_exact_info_from_results(search_results: dict, query: str, together_api_key: str) -> str:
    try:
        client = Together(api_key=together_api_key)
        input_message = f"Extract the exact information from the following search results that directly answers the query: '{query}'\n and respond with no extra text, explanations, or formatting, just the exact query text.\nIf no direct match, return an empty string.\n\nSearch Results:\n{search_results}"

        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            messages=[{
                "role": "user",
                "content": input_message
            }],
        )

        extracted_info = completion.choices[0].message.content

        if not extracted_info:
            return ""

        return extracted_info

    except Exception as e:
        print(f"Error during processing: {e}")
        return ""

if __name__ == '__main__':
    # This section is for testing purposes and requires a .env file with the necessary keys.
    load_dotenv()
    credentials_path = os.getenv("CREDENTIALS_PATH")
    sheet_url = os.getenv("SHEET_URL")
    serp_api_key = os.getenv("SERP_API_KEY")
    together_api_key = os.getenv("TOGETHER_API_KEY")

    if not all([credentials_path, sheet_url, serp_api_key, together_api_key]):
        print("Please set up your .env file with the required variables for testing.")
    else:
        df = csv_to_dataframe('input.csv')
        df2 = sheets_to_dataframe(sheet_url, credentials_path)
        dataframe_to_csv(df, 'output.csv')
        dataframe_to_sheets(df2, sheet_url, credentials_path)

        # Example usage
        input_query = "find me linkedin of {name} who is in pict"

        optimized_query = seo_query_optimizer(input_query, together_api_key)
        print(optimized_query)
        results = get_search_results(optimized_query, serp_api_key)

        result = extract_exact_info_from_results(results, input_query, together_api_key)
        print(result)  

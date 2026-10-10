import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheetLoader:
    def __init__(self, sheet_name, worksheet_name, creds_path):
        self.sheet_name = sheet_name
        self.worksheet_name = worksheet_name
        self.creds_path = creds_path
        self.df = None
    
    def _authorize_google_sheet(self):
        scope = [
            "https://spreadsheets.google.com/feeds", 
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_path, scope)
        client = gspread.authorize(creds)
        return client

    def load_data(self):
        client = self._authorize_google_sheet()
        sheet = client.open(self.sheet_name).worksheet(self.worksheet_name)
        data = sheet.get_all_records()
        self.df = pd.DataFrame(data)
        return self.df
    
    def get_dataframe(self):
        if self.df is not None:
            return self.df
        else:
            raise ValueError("Data has not been loaded yet. Call load_data() first.")
    
    def preview_data(self, num_rows=5):
        if self.df is not None:
            return self.df.head(num_rows)
        else:
            raise ValueError("Data has not been loaded yet. Call load_data() first.")
        
# Example usage

if __name__ == "__main__":
    SHEET_NAME = "tickets1"
    WORKSHEET_NAME = "Sheet1"
    CREDS_PATH = "credentials/service_account.json"
    
    google_sheet_loader = GoogleSheetLoader(SHEET_NAME, WORKSHEET_NAME, CREDS_PATH)
    google_sheet_loader.load_data()
    print(google_sheet_loader.preview_data())
    google_sheet_loader.df.to_csv("data/raw/tickets6.csv", index=False)
    print()
    print("Data saved to 'data/raw/tickets6.csv'.")
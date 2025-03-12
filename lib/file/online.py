import re

apis = [
    "nocodb.com",
    "baserow.io"
]

class ConvertOnlineLink:
    def __init__(self, url):
        self.url = url
        self.found_data = None
        self.found_service = None
        self.is_api = False
        for api in apis:
            if api.strip().lower() in url.strip().lower():
                self.is_api = True
        self.services = []
        for method in dir(self):
            if method.startswith("get_") and method.endswith("_data"):
                self.services.append(method.split("_")[1])
        for service in self.services:
            print('check service:', service)
            service_data = getattr(self, f"get_{service}_data")()
            print(service_data)
            if service_data:
                self.found_data = service_data
                self.found_service = service
                break

    def get_edit_link(self):
        if self.found_service:
            return getattr(self, f"edit_link_{self.found_service}")()
    def get_download_link(self):
        if self.found_service:
            return getattr(self, f"download_link_{self.found_service}")()

    def get_googlesheet_data(self):
        spreadsheet_ids = re.findall("docs\.google.com\/spreadsheets\/d\/(.*?)\/", self.url)
        return spreadsheet_ids[0] if spreadsheet_ids else None
    def edit_link_googlesheet(self):
        return f"https://docs.google.com/spreadsheets/d/{self.found_data}/edit"
    def download_link_googlesheet(self):
        return f"https://docs.google.com/spreadsheets/d/{self.found_data}/export?format=csv"

    def get_zohosheet_data(self):
        spreadsheet_ids = re.findall("sheet\.zohopublic\.com\/sheet\/published\/(.*?)($|\?)", self.url)
        return spreadsheet_ids[0][0] if spreadsheet_ids else None
    # Note, zoho publish doesn't allow editing
    def edit_link_zohosheet(self):
        return f"https://sheet.zohopublic.com/sheet/published/{self.found_data}"
    def download_link_zohosheet(self):
        return f"https://sheet.zohopublic.com/sheet/published/{self.found_data}?download=csv&sheetname=cards"
    
    # For grist, copy the link to the csv export for the specific sheet
    # Doesn't support multiple grist views/databases in a single grist page
    def get_grist_data(self):
        # https://api.getgrist.com/o/docs/api/docs/j7uxf2UBTwd7kFvAogrLU1/download/csv?viewSection=6&tableId=Cardsv2&activeSortSpec=%5B%5D&filters=%5B%5D&linkingFilter=%7B%22filters%22%3A%7B%7D%2C%22operations%22%3A%7B%7D%7D
        spreadsheet_ids = re.findall("api\.getgrist\.com\/o\/docs\/api\/docs\/(.*?)($|\/)", self.url)
        return spreadsheet_ids[0][0] if spreadsheet_ids else None
    def edit_link_grist(self):
        return f"https://docs.getgrist.com/{self.found_data}/"
    def download_link_grist(self):
        return self.url
    
    # TODO NOCODB - this can only be accessed via api
    # edit: https://app.nocodb.com/#/base/4bf4f19c-e882-498c-bc2a-2d27d897d4bc
    # embed: https://nocodb-nocodb-rsyir.ondigitalocean.app/dashboard/#/nc/base/e3bba9df-4fc1-4d11-b7ce-41c4a3ad6810?embed
    # table id: mviul4wkjjv62oj
    # token: XX28GJ86Z_mCTpLJqIFErWAe6i8jbh6HYlGUTMFO
    def get_nocodb_data(self):
        spreadsheet_ids = re.findall("app\.nocodb\.com\/\#\/base\/(.*?)($|\/)", self.url)
        return spreadsheet_ids[0][0] if spreadsheet_ids else None
    def edit_link_nocodb(self):
        return f"https://app.nocodb.com/#/base/{self.found_data}"
    def download_link_nocodb(self):
        return None
    
    # TODO baserow - probably api

    # TODO ironcalc - self-hosted, xls only (no csv)

    # TODO rows.com - probably api

    # TODO excel online?
    
# TODO enable api access for some spreadsheet connectivity
# Instead of CSVData, it should be APIData
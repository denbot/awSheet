def auto_resize_columns(sheets_service, file_id, sheet_id, start_index, end_index):
    # Auto-resize the dimensions of the specified columns to fit the widest cell value
    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=file_id,
        body={
            "requests": [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": start_index,
                            "endIndex": end_index
                        }
                    }
                }
            ]
        }
    ).execute()

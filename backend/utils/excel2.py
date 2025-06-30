import pandas as pd
from datetime import datetime
import os
from dateutil import parser
import re
from typing import Tuple, List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExcelToCSVConverter:
    """A class to handle Excel to CSV conversion with multiple sheets processing."""
    
    def __init__(self):
        self.date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')


   
    def process_excel_to_csv(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Main method to process an Excel file into a pipe-separated CSV file.
        
        Args:
            input_path: Path to the input Excel file
            output_path: Path to save the output CSV file
            
        Returns:
            Tuple of (success_flag, output_path_or_error_message)
        """
        try:
            # Step 1: Validate input file
            self._validate_input_file(input_path)
            
            # Step 2: Read and process all sheets
            combined_data = self._process_all_sheets(input_path)
            
            # Step 3: Write output file
            self._write_output_file(combined_data, output_path)
            
            logger.info(f"Successfully created CSV file at {output_path}")
            return True, output_path,input_path

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def _validate_input_file(self, input_path: str) -> None:
        """Validate that the input file exists and is accessible."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found at {input_path}")
        if not input_path.lower().endswith(('.xlsx', '.xls')):
            raise ValueError("Input file must be an Excel file (.xlsx or .xls)")
    
    def _process_all_sheets(self, input_path: str) -> List[str]:
        """Process all sheets in the Excel file and return combined data."""
        combined_data = []
        
        with pd.ExcelFile(input_path) as xls:
            for sheet_name in xls.sheet_names:
                logger.info(f"Processing sheet: {sheet_name}")
                
                # Step 1: Read sheet data
                df = self._read_sheet_data(xls, sheet_name)
                
                # Step 2: Process data with sheet-specific handling
                sheet_data = self._process_sheet(df, sheet_name)
                combined_data.extend(sheet_data)
                
        return combined_data
    
    def _read_sheet_data(self, xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
        """Read a single sheet from Excel file with proper handling."""
        try:
            # Read sheet with all columns as strings to preserve formatting
            return pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        except Exception as e:
            logger.warning(f"Error reading sheet {sheet_name}: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame if sheet can't be read
    
    def _process_sheet(self, df: pd.DataFrame, sheet_name: str) -> List[str]:
        """Process a single sheet DataFrame with sheet-specific handling."""
        if df.empty:
            return []
            
        # Step 1: Format date columns
        df = self._format_date_columns(df)
        
        # Step 2: Process each row with sheet-specific handling
        return self._process_dataframe_rows(df, sheet_name)
    
    def _format_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format date columns to DD-MMM-YYYY format."""
        for col in df.columns:
            if df[col].empty:
                continue
                
            # Check if column contains date-like values
            if self._is_date_column(df[col]):
                try:
                    df[col] = df[col].apply(self._parse_and_format_date)
                    logger.debug(f"Formatted date column: {col}")
                except Exception as e:
                    logger.warning(f"Skipping column {col} due to error: {e}")
                    
        return df
    
    def _is_date_column(self, series: pd.Series) -> bool:
        """Determine if a column contains date-like values."""
        sample_value = series.iloc[0] if not series.empty else None
        
        if isinstance(sample_value, (datetime, pd.Timestamp)):
            return True
        elif isinstance(sample_value, str) and self.date_pattern.match(sample_value):
            return True
        return False
    
    def _parse_and_format_date(self, value) -> str:
        """Parse and format a date value."""
        if pd.isna(value):
            return ''
            
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.strftime('%d-%b-%Y')
        elif isinstance(value, str) and self.date_pattern.match(value):
            return parser.parse(value).strftime('%d-%b-%Y')
        return value
    
    def _process_dataframe_rows(self, df: pd.DataFrame, sheet_name: str) -> List[str]:
        """Process DataFrame rows into pipe-separated strings with sheet-specific handling."""
        processed_rows = []
        
        for _, row in df.iterrows():
            processed_values = []
            for i, value in enumerate(row):
                # Get column name for context (if available)
                col_name = df.columns[i] if i < len(df.columns) else str(i)
                
                # Process with sheet-specific handling
                processed_value = self._process_cell_value(value, sheet_name, col_name)
                processed_values.append(processed_value)
            
            processed_rows.append('|'.join(processed_values))
            
        return processed_rows
    
    def _process_cell_value(self, value, sheet_name: str, col_name: str) -> str:
        """Process a single cell value with standardized formatting and sheet-specific rules."""
        if pd.isna(value):
            return ''
            
        str_value = str(value).strip()
        
        # Remove commas and normalize whitespace
        str_value = str_value.replace(',', '').strip()
        str_value = ' '.join(str_value.split())
        
        # Apply specific formatting rules with sheet-specific handling
        return self._apply_formatting_rules(str_value, sheet_name, col_name)
    
    def _apply_formatting_rules(self, value: str, sheet_name: str, col_name: str) -> str:
        """Apply specific formatting rules to a value with sheet-specific handling."""
        # Sheet-specific handling for IDN sheet
        if sheet_name.upper() == 'IDN':
            return self._handle_idn_sheet_values(value, col_name)
            
        # Standard formatting for other sheets
        return self._standard_formatting(value)
    
    def _handle_idn_sheet_values(self, value: str, col_name: str) -> str:
        """Special handling for IDN sheet values."""
        # Check if this is an Aadhar number column (you may need to adjust this condition)
        if 'AADHAR' in col_name.upper() or (value.isdigit() and len(value) <= 12):
            # Pad with leading zeros to make 12 digits if it's a number <= 12 digits
            if value.isdigit():
                return value.zfill(12)
            return value
            
        # Check if this is a PAN number column
        elif 'PAN' in col_name.upper() or (len(value) == 10 and value.isalnum()):
            # PAN numbers should be in uppercase
            return value.upper()
            
        return self._standard_formatting(value)
    
    def _standard_formatting(self, value: str) -> str:
        """Apply standard formatting rules to a value."""
        # Handle special cases
        if value == "91":
            return "+91"
            
        # Standardize gender values
        value_lower = value.lower()
        if value_lower == "male":
            return "MALE"
        elif value_lower == "female":
            return "FEMALE"
            
        # Standardize title values
        if value_lower in ["mr.", "mr"]:
            return "MR"
        elif value_lower in ["ms", "ms."]:
            return "MS"
            
        # Handle numeric values
        return self._format_numeric_values(value)
    
    def _format_numeric_values(self, value: str) -> str:
        """Format numeric values consistently."""
        try:
            # Preserve leading zeros for numeric strings
            if value.lstrip('0') == '':
                return value.zfill(1)  # At least one zero
                
            if value.startswith('0') and '.' not in value:
                return value  # Preserve leading zeros for integer strings
                
            float_val = float(value)
            if float_val.is_integer():
                return str(int(float_val))
            return f"{float_val:.2f}"
        except ValueError:
            return value
    
    def _write_output_file(self, data: List[str], output_path: str) -> None:
        """Write the processed data to output file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(data))

def main():
    converter = ExcelToCSVConverter()
    
    excel_file_path = 'SK_20250531 Bulk - Copy.xlsx'  #D:\First\Project\SK_20250531 Bulk - Copy.xlsx
    output_file_path = 'pipe_separated_file2.csv'
    
    if not os.path.exists(excel_file_path):
        logger.error(f"Error: File not found at {excel_file_path}")
        logger.error(f"Current working directory: {os.getcwd()}")
        return
        
    success, result = converter.process_excel_to_csv(excel_file_path, output_file_path)
    if not success:
        logger.error(result)
        

if __name__ == '__main__':
    main()
    
    
    
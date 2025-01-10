import xmltodict
import json
import base64
import os

class FileProcessor:
    def __init__(self, input_txt_file, target_json_file, output_xml_file, output_json_file,result_json_file):
        self.input_txt_file = input_txt_file
        self.target_json_file = target_json_file
        self.output_xml_file = output_xml_file
        self.output_json_file = output_json_file
        self.result_json_file = result_json_file

    def load_json_from_file(self, file_path):
        """Helper function to load JSON data from a file"""
        with open(file_path, 'r', encoding="utf-8") as file:
            return json.load(file)

    def save_json_to_file(self, data, file_path):
        """Helper function to save JSON data to a file"""
        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def decode_base64_content(self):
        """Decode base64 content from input text file"""
        with open(self.input_txt_file, "r") as file:
            txt = file.read()
            tojson = json.loads(txt)  # Load JSON from text
            r = tojson['response']['documents'][0]['value']
            document_data = r.encode('utf-8') + b'=='  # Prepare base64 data for decoding
            decoded = base64.urlsafe_b64decode(document_data)
        
        # Save the decoded content as an XML file
        with open(self.output_xml_file, 'w', encoding="utf-8") as output_file:
            output_file.write(decoded.decode("utf-8"))
        print(f"Decoded XML saved to {self.output_xml_file}")

    def parse_xml_to_json(self):
        """Parse XML and convert it to JSON format"""
        with open(self.output_xml_file, "r", encoding="utf-8") as xml_file:
            data_dict = xmltodict.parse(xml_file.read())
        
        # Wrap the object in the "BIR" key into an array
        if not isinstance(data_dict['BIR']['BIR'], list):
            data_dict['BIR']['BIR'] = [data_dict['BIR']['BIR']]  # Wrap the BIR object in a list

        # Convert the parsed XML data to JSON and save
        self.save_json_to_file(data_dict, self.output_json_file)
        print(f"Parsed XML to JSON and saved to {self.output_json_file}")

    

    def update_target_json(self):
        """Update the target JSON using data from source JSON"""
        target_json = self.load_json_from_file(self.target_json_file)
        source_json = self.load_json_from_file(self.output_json_file)

        # Loop through the segments in the target JSON and replace values from the source JSON
        for target_segment, source_segment in zip(target_json['response']['segments'], source_json['BIR']['BIR']):
            # Check for the key 'bdb' or 'BDB' and assign it to target
            if 'bdb' in source_segment:
                target_segment['bdb'] = source_segment['bdb']
            elif 'BDB' in source_segment:
                target_segment['bdb'] = source_segment['BDB']
            
            # Update the 'Score' from the source to the target and convert to integer
            if 'BDBInfo' in source_segment and 'Quality' in source_segment['BDBInfo']:
                source_score = source_segment['BDBInfo']['Quality'].get('Score', None)
                if source_score is not None:
                    try:
                        target_segment['bdbInfo']['quality']['score'] = int(source_score)
                    except ValueError:
                        print(f"Error: Invalid score value '{source_score}' for segment, skipping...")

            # Update the 'Type' and 'Subtype' from the source to the target
            if 'BDBInfo' in source_segment:
                source_type = source_segment['BDBInfo'].get('Type', None)
                if source_type is not None:
                    target_segment['bdbInfo']['type'] = [source_type.upper()]

                source_subtype = source_segment['BDBInfo'].get('Subtype', None)
                if source_subtype is not None:
                    target_segment['bdbInfo']['subtype'] = source_subtype.split()
                else:
                    target_segment['bdbInfo']['subtype'] = []

            # Update the 'CreationDate' from the source to the target
            if 'BDBInfo' in source_segment:
                source_creation_date = source_segment['BDBInfo'].get('CreationDate', None)
                if source_creation_date is not None:
                    target_segment['bdbInfo']['creationDate'] = source_creation_date

            # Update the 'format:type' from the source to the target
            if 'BDBInfo' in source_segment:
                source_type_format = source_segment['BDBInfo'].get('Format', {}).get('Type', None)
                if source_type_format is not None:
                    target_segment['bdbInfo']['format']['type'] = source_type_format

        # Save the updated target JSON to a new file with the input file name (without .txt extension)
        result_folder = "result"
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)
        
        # Extract the input file name without the .txt extension
        output_json_filename = os.path.splitext(os.path.basename(self.input_txt_file))[0] + "_updated_target_file.json"
        output_json_path = os.path.join(result_folder, output_json_filename)
        
        self.save_json_to_file(target_json, output_json_path)
        print(f"Target JSON updated and saved to {output_json_path}")

    def delete_xml_file(self):
        """Delete the output XML file after processing"""
        if os.path.exists(self.output_xml_file):
            os.remove(self.output_xml_file)
            print(f"Deleted temporary XML file: {self.output_xml_file}")
        else:
            print(f"XML file not found for deletion: {self.output_xml_file}")

    def delete_testjson_file(self):
        """Delete the output JSON file after processing"""
        if os.path.exists(self.output_json_file):
            os.remove(self.output_json_file)
            print(f"Deleted temporary Json file: {self.output_json_file}")
        else:
            print(f"JSON file not found for deletion: {self.output_json_file}")

    def remove_empty_entry(self):
        """Remove empty values in 'bdb' from the output JSON and replace the file in 'result' folder."""
        # Select the first JSON file in the 'result' folder
        result_folder = "result"
        dir_list = os.listdir(result_folder)

        if not dir_list:
            print("No files found in the 'result' folder.")
            return  # Exit if no files found

        # Filter the list to get only JSON files
        json_files = [f for f in dir_list if f.endswith('.json')]
        if not json_files:
            print("No JSON files found in the 'result' folder.")
            return  # Exit if no JSON files found

        # Select the first JSON file from the list
        output_json_file = os.path.join(result_folder, json_files[0])
        print(f"Selected JSON file for modification: {output_json_file}")

        # Load the result JSON from the selected file
        result_json = self.load_json_from_file(output_json_file)

        if result_json is None:
            print(f"Error loading JSON from {output_json_file}.")
            return  # Exit if the JSON file could not be loaded

        # Filter segments that have non-empty 'bdb' values
        filtered_segments = [segment for segment in result_json["response"]["segments"] if segment.get("bdb")]

        # Update the data with the filtered segments
        result_json["response"]["segments"] = filtered_segments

        # Overwrite the existing file in the result folder with the filtered data
        self.save_json_to_file(result_json, output_json_file)  # Save back with the same filename

        print(f"Filtered data has been written to {output_json_file}")



def main():
    # Get the list of files in the 'input' folder
    input_folder = "input"
    files_in_input = os.listdir(input_folder)

    # Filter the files if needed (e.g., only text files)
    txt_files = [f for f in files_in_input if f.endswith(".txt")]

    if not txt_files:
        print("No text files found in the 'input' folder.")
        return

    # Select the first available text file (or modify this logic as needed)
    dynamic_filename = txt_files[0]
    input_txt_file_path = os.path.join(input_folder, dynamic_filename)



    # Initialize the FileProcessor class with the dynamically selected file
    processor = FileProcessor(
        input_txt_file=input_txt_file_path,
        target_json_file="TEMPLATE.json",
        output_xml_file="output.xml",
        output_json_file="test.json",
        result_json_file=""
    )
    
    # Run the process
    processor.decode_base64_content()
    processor.parse_xml_to_json()
    processor.update_target_json()
   
    # Perform filtering and removal of empty entries in 'bdb'
    processor.remove_empty_entry()

    # Delete the XML file after all processing is done
    processor.delete_xml_file()
    processor.delete_testjson_file()

 

if __name__ == "__main__":
    main()

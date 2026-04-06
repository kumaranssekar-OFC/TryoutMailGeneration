import os
import glob
import pandas as pd
import re
import math
from jira import JIRA

# Assuming JiraAccess is a class that handles JIRA authentication and provides a JIRA object
# If it's a function that returns a JIRA object, adjust accordingly.
from JiraAccess import jira_access # Assuming this is correctly implemented


__version__ = "01.00"

# --- Constants ---
# It's good practice to define constants at the module level or within the class
# if they are specific to the class.
DESCRIPTION_FILE = "Text2.txt"
EXTRACTED_JIRA_DATA_FILE = "Text3.txt"
IMAGE_OVERVIEW_BASE_PATH = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan"
SERVER_LOCATIONS = ["0046", "0047", "0048", "0049"]

# Define JIRA custom field IDs and other JIRA-specific constants
JIRA_SUMMARY_FIELD = 'summary'
JIRA_CUSTOM_FIELD_10042 = 'customfield_10042'
JIRA_DESCRIPTION_FIELD = 'description'

# Define special characters for cleaning task names
SPECIAL_CHARS_FOR_TASK_NAME = ["@", ",", "/", "(", ")"]

# Define Hyperflash mapping for A-IVI2 / CCS boards
HYPERFLASH_MAPPING = {
    "030D11": ["sbr_pm02", "flash_image_nissan-aivi2-c3-3gb.bin"],
    "030E11": ["sbr_pm02", "flash_image_nissan-aivi2-c3.bin"],
    "031311": ["sbr_m3_j32v_pm01", "flash_image_nissan-aivi2-j32v-c0.bin"],
    "031511": ["sbr_lattice_pm02", "flash_image_nissan-aivi2-c3-cpld.bin"],
    "031811": ["sbr_lattice_pm02", "flash_image_nissan-aivi2-b.bin"],
    "031611": ["CPLD_PEXT_SBR_M3_CCS11_PM01", "flash_image_nissan-aivi2-ccs11-b.bin"]
}

# Mapping for JIRA table headers and column counts based on scope
JIRA_TABLE_DEFINITIONS = {
    "A-IVI2": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6},
    "CCS1.1": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6},
    "CCS 1.5": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6},
    "P-IVI2": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6},
    "P-IVI": {"header": "||HW||BoardID||Image||owned by||SW; Remarks||\n", "cols": 5},
    "DEFAULT": {"header": "||HW||BoardID||Image||owned by||SW; Remarks||\n", "cols": 5}
}


class JiraIssueCreator:
    """
    A class to create and update JIRA sub-tasks based on an input Excel file,
    extracting information from JIRA descriptions and local file paths.
    """

    def __init__(self):
        self.df_init = None
        self.task_issue_id = None
        self.to_task_issue_id = None
        self.task_name = None
        self.task_type = None
        self.task_sw = None
        self.part_numbers = None  # Renamed from part_number to plural for clarity
        self._no_of_partnumbers = 0
        self.collection_id = None
        self.base_sw = None
        self.extracted_data1 = ""
        self.extracted_data2 = ""
        self._jira_description_content = ""
        self.emmc_details = []
        self.part_details = []
        self.jira_client = None # To store the JIRA client object

    def _get_jira_client(self):
        """Initializes and returns the JIRA client."""
        if self.jira_client is None:
            self.jira_client = jira_access() # Assuming jira_access() returns a JIRA client
        return self.jira_client

    def read_input_excel(self, file_path="init.xlsx", sheet_name="init"):
        """
        Reads input data from an Excel file.
        """
        try:
            self.df_init = pd.read_excel(file_path, sheet_name=sheet_name)
            return True
        except FileNotFoundError:
            print(f"Error: Input Excel file '{file_path}' not found.")
            return False
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return False

    def set_task_inputs(self):
        """
        Extracts and sets task-related attributes from the initialized DataFrame.
        """
        if self.df_init is None:
            print("Error: Input data not loaded. Call read_input_excel first.")
            return False

        try:
            # Using .iloc[0] for single row access, more robust than [0]
            self.task_issue_id = str(self.df_init['Jira_Main_Task '].iloc[0]).strip()
            self.to_task_issue_id = str(self.df_init['Jira_TO_Task'].iloc[0]).strip()
            self.task_name = str(self.df_init['Task_Name'].iloc[0]).strip()
            self.task_type = str(self.df_init['Release_Type'].iloc[0]).strip()
            self.task_sw = str(self.df_init['SW_Version'].iloc[0]).strip()
            self.part_numbers = self.df_init['Part_Numbers'].dropna().tolist() # Convert Series to list, drop NaNs
            self._no_of_partnumbers = len(self.part_numbers)
            self.collection_id = str(self.df_init['Docushare_CollectionID'].iloc[0]).strip()
            self.base_sw = self.df_init['Base_SW'].tolist()

            print(f"Task type: {self.task_type}")
            print(f"Part numbers: {self.part_numbers}")
            return True
        except KeyError as e:
            print(f"Error: Missing expected column in Excel file: {e}")
            return False
        except IndexError:
            print("Error: Input Excel sheet is empty or does not contain enough rows.")
            return False
        except Exception as e:
            print(f"Error setting task inputs: {e}")
            return False

    def _clean_task_name(self, name):
        """Removes special characters from a task name for regex use."""
        for char in SPECIAL_CHARS_FOR_TASK_NAME:
            name = name.replace(char, r"\W") # Use raw string for regex
        return name.replace(" ", r"\s") # Use raw string for regex

    def extract_jira_description(self):
        """
        Extracts the description from the main JIRA task and processes it
        to find relevant sections based on task name and type.
        """
        jira_client = self._get_jira_client()
        try:
            main_issue = jira_client.issue(self.task_issue_id)
            description = main_issue.fields.description

            if not description:
                print(f"Warning: No description found for JIRA issue {self.task_issue_id}")
                return False

            with open(DESCRIPTION_FILE, "w", encoding="utf-8") as f_desc:
                f_desc.write(description)

            cleaned_task_name_for_regex = self._clean_task_name(self.task_name)
            reflash_check = False
            relevant_lines = []

            with open(DESCRIPTION_FILE, "r", encoding="utf-8") as f_desc:
                lines = f_desc.readlines()
                for i, line in enumerate(lines):
                    # Use regex for more flexible matching
                    if re.search(cleaned_task_name_for_regex, line, re.IGNORECASE):
                        print(f"Task name '{self.task_name}' found on line {i}")
                        normalized_line = line.lower().replace("re-flash", "reflash")

                        is_reflash_type = ("reflash" in normalized_line)
                        is_splupd_type = (self.task_type == "SplUpd")

                        if is_splupd_type and is_reflash_type:
                            reflash_check = True
                            relevant_lines = self._find_device_details_in_description(lines, i)
                            break
                        elif not is_splupd_type and not is_reflash_type: # Non-SplUpd and not reflash
                            reflash_check = True
                            relevant_lines = self._find_device_details_in_description(lines, i)
                            break
                        # If SplUpd but not reflash or non-SplUpd but is reflash, continue searching
                
                if not reflash_check:
                    print(f"Warning: No matching section found for task name '{self.task_name}' and type '{self.task_type}'.")
                    return False

            if not relevant_lines:
                print(f"Warning: No device details extracted for '{self.task_name}'. SW might be incorrect.")
                return False

            with open(EXTRACTED_JIRA_DATA_FILE, "w", encoding="utf-8") as f_extracted:
                for line in relevant_lines:
                    # Clean the line and write it
                    cleaned_line = line.replace("|", "").replace("(/)", "").replace("(-)", "").replace("\n", "").replace("(x)", "").replace("(!)", "").replace("*", "").strip()
                    if cleaned_line: # Only write non-empty lines
                        f_extracted.write(cleaned_line + "\n")

            with open(EXTRACTED_JIRA_DATA_FILE, "r", encoding="utf-8") as f_extracted:
                self._jira_description_content = f_extracted.read()
            return True

        except JIRA.exceptions.JIRAError as e:
            print(f"JIRA Error accessing issue {self.task_issue_id}: {e}")
            return False
        except Exception as e:
            print(f"Error extracting JIRA description: {e}")
            return False

    def _find_device_details_in_description(self, lines, start_index):
        """
        Helper method to find and extract 'Devices' section from the JIRA description.
        """
        dev_expected = "Devices"
        extracted_lines = []
        
        try:
            # Look for SW version
            sw_found_index = -1
            for i in range(start_index, len(lines)):
                if self.task_sw in lines[i]:
                    sw_found_index = i
                    break
            
            if sw_found_index == -1:
                print(f"Warning: SW version '{self.task_sw}' not found after task name in description.")
                return []

            # Look for "Devices" keyword after SW version
            devices_found_index = -1
            for i in range(sw_found_index, len(lines)):
                if dev_expected in lines[i]:
                    devices_found_index = i
                    break

            if devices_found_index == -1:
                print(f"Warning: '{dev_expected}' section not found after SW version in description.")
                return []

            # Extract lines after "Devices" section
            # skip_section points to the line after "Devices" header
            skip_section = devices_found_index + 2 # Assuming two lines after "Devices" before content starts
            
            # Estimate total lines for part numbers (each part number may take multiple lines)
            # This logic seems a bit fragile if the format varies
            total_no_lines_to_read = self._no_of_partnumbers * 2 # Heuristic, adjust if necessary

            for i in range(total_no_lines_to_read):
                line_index = skip_section + i
                if line_index < len(lines):
                    extracted_lines.append(lines[line_index])
                else:
                    print(f"Warning: Reached end of description while extracting device details. Expected {total_no_lines_to_read} lines but found less.")
                    break
            
            return extracted_lines

        except Exception as e:
            print(f"Error in _find_device_details_in_description: {e}")
            return []

    def read_tryout_mail_file(self):
        """
        Reads content from a tryout mail file (named after SW version)
        and extracts specific data.
        """
        try:
            file_name = f"{self.task_sw}.txt"
            with open(file_name, 'r', encoding="utf-8") as f_mail:
                content = f_mail.read()

            start_used = content.find("Used for ")
            if start_used == -1:
                print(f"Warning: 'Used for ' not found in '{file_name}'.")
                return

            end_adr = content.find(r"\ADR3", start_used)
            if end_adr == -1:
                print(f"Warning: '\\ADR3' not found after 'Used for ' in '{file_name}'.")
                return

            self.extracted_data1 = content[start_used + len("Used for "): end_adr + len(r"\ADR3")].strip()

            start_pd = content.find("PD Configuration ")
            if start_pd == -1:
                print(f"Warning: 'PD Configuration ' not found in '{file_name}'.")
                return
            
            # Extract from PD Configuration to the end of the file
            self.extracted_data2 = content[start_pd + len("PD Configuration "):].strip()

        except FileNotFoundError:
            print(f"Warning: Tryout mail file '{self.task_sw}.txt' not found. SUB-Input section in Task will not be updated.")
        except Exception as e:
            print(f"Error reading tryout mail file: {e}")

    def _get_sw_stamp_and_image_path(self, sw_name, location):
        """Helper to get SW stamp and image path for a given SW name and server location."""
        sw_path_base = os.path.join(IMAGE_OVERVIEW_BASE_PATH, f"{location}_RN_AIVI_7513750800", "00_SW", "_Versions", sw_name, "IMX6")
        
        if not os.path.exists(sw_path_base):
            return None, None

        sw_stamp_files = glob.glob(os.path.join(sw_path_base, "*.lnk"))
        if not sw_stamp_files:
            return None, None

        sw_stamp = os.path.splitext(os.path.basename(sw_stamp_files[0]))[0]
        image_resides_path = os.path.join(IMAGE_OVERVIEW_BASE_PATH, f"{location}_RN_AIVI_7513750800", "00_SW", "Production", sw_stamp, "Release")
        
        if not os.path.exists(image_resides_path):
            return None, None

        image_file_pattern = f"images_overview_{sw_name[:4]}.txt"
        image_files = glob.glob(os.path.join(image_resides_path, image_file_pattern))
        
        if not image_files:
            return None, None

        return sw_stamp, image_files[0] # Return the first found image file path

    def _process_image_overview_file(self, image_file_path, part_number):
        """Helper to extract EMMC and part details from an image overview file."""
        if not os.path.exists(image_file_path):
            print(f"Warning: Image overview file not found: {image_file_path}")
            return

        with open(image_file_path, "r", encoding="utf-8") as read_iot:
            for line in read_iot:
                if part_number in line and "-> use" not in line:
                    split_pn_line = line.split()
                    if not split_pn_line:
                        continue

                    # Determine if the line starts with a space to adjust indexing
                    line_starts_with_space = line.startswith(" ")

                    try:
                        pn_index = split_pn_line.index(part_number)

                        if not line_starts_with_space:
                            # Original logic for non-space-started lines
                            pn = split_pn_line[pn_index]
                            emmc = split_pn_line[pn_index + 3]
                            map_cut = split_pn_line[pn_index + 8]
                            map_version = split_pn_line[pn_index + 9].replace(",", "")
                        else:
                            # Original logic for space-started lines
                            pn = split_pn_line[pn_pn_index] # Should be pn_index, typo in original?
                            emmc = split_pn_line[pn_index + 1]
                            map_cut = split_pn_line[pn_index + 6]
                            map_version = split_pn_line[pn_index + 7].replace(",", "")
                        
                        self.part_details.append(f"{pn} {map_cut} {map_version}")
                        self.emmc_details.append(f"{pn} {emmc}")
                        # Found details for this part number, move to next
                        break 
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not parse line for part number '{part_number}' in '{image_file_path}'. Error: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred while processing image overview: {e}")

    def read_image_overview(self):
        """
        Reads image overview files to extract part and EMMC details.
        Handles both 'SplUpd' and other task types.
        """
        self.emmc_details = []
        self.part_details = []
        
        part_sw_map = {}
        # Assuming self.part_numbers and self.base_sw are aligned
        for i in range(len(self.part_numbers)):
            if str(self.part_numbers[i]) != "nan": # Ensure part number is valid
                part_sw_map[self.part_numbers[i]] = self.base_sw[i]
        
        print("Part to Base SW mapping:", part_sw_map)

        processed_part_numbers = set() # To avoid processing same part number multiple times if found in different files

        if self.task_type == "SplUpd":
            for part_number, sw_name in part_sw_map.items():
                if part_number in processed_part_numbers:
                    continue
                for location in SERVER_LOCATIONS:
                    _, image_file_path = self._get_sw_stamp_and_image_path(sw_name, location)
                    if image_file_path:
                        self._process_image_overview_file(image_file_path, part_number)
                        processed_part_numbers.add(part_number)
                        break # Found for this part number, move to next location/part
        else: # For other task types, use self.task_sw
            for location in SERVER_LOCATIONS:
                _, image_file_path = self._get_sw_stamp_and_image_path(self.task_sw, location)
                if image_file_path:
                    for part_number in self.part_numbers:
                        if part_number in processed_part_numbers or str(part_number) == "nan":
                            continue
                        self._process_image_overview_file(image_file_path, part_number)
                        processed_part_numbers.add(part_number)
                    if processed_part_numbers: # If any part numbers were found, we can break from locations
                        break 
        
        # Filter out "No_Map ()" entries
        self.part_details = [entry for entry in self.part_details if "No_Map ()" not in entry]
        print("Final Part Details:", self.part_details)
        print("Final EMMC Details:", self.emmc_details)


    def _determine_dev_prd(self, task_name_parts):
        """Determines if the task is DEV or PRD based on TSB/DSB in task name."""
        for part in task_name_parts:
            if "TSB" in part.upper() or "DSB" in part.upper():
                return "DEV"
        return "PRD"

    def _get_jira_table_definition(self, task_name_parts):
        """Returns the JIRA table header and column count based on task scope."""
        for part in task_name_parts:
            if part in JIRA_TABLE_DEFINITIONS:
                return JIRA_TABLE_DEFINITIONS[part]
        return JIRA_TABLE_DEFINITIONS["DEFAULT"]

    def _prepare_emmc_mapping(self):
        """Prepares a dictionary mapping part numbers to their EMMC values."""
        emmc_map = {pn: [] for pn in self.part_numbers if str(pn) != "nan"}
        for item in self.emmc_details:
            for pn in emmc_map:
                if item.startswith(str(pn)):
                    # Extract the part after the first colon and strip leading space
                    emmc_value = item.split(': ')[1] if ': ' in item else item.split(str(pn))[1].strip()
                    emmc_map[pn].append(emmc_value)
                    break
        
        # Remove any entries that are empty lists (no EMMC found for that PN)
        return {k: v for k, v in emmc_map.items() if v}


    def _build_jira_table_rows(self, emmc_map, table_def, dev_prd, scope):
        """Constructs the rows for the JIRA table."""
        table_rows = []
        board_id_notes = [] # For A-IVI2/CCS hyperflash notes

        mapping_table = str.maketrans({'[': '', ']': '', ',': '', "'": '', ')': '', '(': ''})

        for part_number, emmc_values in emmc_map.items():
            for emmc_value in emmc_values: # A single PN might have multiple EMMC values in complex cases
                # Example: emmc_value could be "PN123_030D11: SBR_NISSAN_C3.img"
                # Need to extract BoardID like "030D11" and EMMC image name "SBR_NISSAN_C3.img"
                
                parts = emmc_value.split(':')
                if len(parts) < 2:
                    print(f"Warning: Unexpected EMMC format for '{emmc_value}'. Skipping.")
                    continue

                emmc_id_and_image = parts[0].strip()
                emmc_image_name = parts[1].strip()

                # Extract BoardID from emmc_id_and_image (e.g., "PN123_030D11" -> "030D11")
                board_id_match = re.search(r'_([0-9A-Za-z]{6})$', emmc_id_and_image)
                emmc_board_id = board_id_match.group(1) if board_id_match else "UNKNOWN_BOARD_ID"


                if scope in ["A-IVI2", "CCS1.1", "CCS 1.5", "P-IVI2"]:
                    hyperflash_info = HYPERFLASH_MAPPING.get(emmc_board_id)
                    if hyperflash_info:
                        hf_gnss = hyperflash_info[0]
                        hf_image = hyperflash_info[1]
                        row_content = (
                            f"|{part_number} |{emmc_board_id} | {hf_image} | {emmc_image_name}| {hf_gnss} | "
                            f"SW_{self.task_sw.split('_')[0]}_{dev_prd}; \n "
                            f"TryOut: (?)(?) \n Config: (?) \n CheckSums: (?) \n DS: (?) \n  |"
                        )
                        board_id_notes.append(f"*{emmc_board_id}* : {hf_image}")
                    else:
                        print(f"Warning: No hyperflash info found for BoardID '{emmc_board_id}'. Using default format.")
                        # Fallback to default if no hyperflash info
                        row_content = (
                            f"|{part_number} |{emmc_board_id} | {emmc_image_name}|[~mkr2hi]| "
                            f"SW_{self.task_sw.split('_')[0]}_{dev_prd}; \n "
                            f"TryOut: (?)(?) \n Config: (?) \n CheckSums: (?) \n DS: (?) \n  |"
                        )
                else: # Default case for P-IVI and others
                    row_content = (
                        f"|{part_number} |{emmc_board_id} | {emmc_image_name}|[~mkr2hi]| "
                        f"SW_{self.task_sw.split('_')[0]}_{dev_prd}; \n "
                        f"TryOut: (?)(?) \n Config: (?) \n CheckSums: (?) \n DS: (?) \n  |"
                    )
                table_rows.append(row_content)
        return "\n".join(table_rows), "\n".join(board_id_notes)


    def update_jira_task(self):
        """
        Constructs the JIRA description and updates the JIRA sub-task.
        """
        jira_client = self._get_jira_client()
        try:
            iss_upd = jira_client.issue(self.to_task_issue_id)

            task_name_parts = self.task_name.split()
            dev_prd = self._determine_dev_prd(task_name_parts)
            
            table_def = self._get_jira_table_definition(task_name_parts)
            table_header = table_def["header"]
            
            emmc_map = self._prepare_emmc_mapping()
            table_rows, board_id_notes_content = self._build_jira_table_rows(emmc_map, table_def, dev_prd, task_name_parts[0]) # Assuming scope is the first part of task_name

            # Determine JIRA summary
            if self.task_type == "SplUpd":
                summary = f"Perform Reflash Try-Out with SW {self.task_sw} ({self.task_name})"
            else:
                summary = f"Perform Internal Try-Out with SW {self.task_sw} ({self.task_name})"

            # Determine scope and Board Note
            scope = "A-IVI" # Default scope
            board_note_prefix = ""
            for part in task_name_parts:
                if part in ["P-IVI", "A-IVI2", "CCS1.1", "CCS 1.5", "P-IVI2"]:
                    scope = part
                    if scope != "P-IVI": # Only add note for A-IVI2/CCS types
                        board_note_prefix = "BoardID – Hyperflash file name assignment for the release to production \n"
                    break
            
            full_board_note = f"{board_note_prefix}{board_id_notes_content}" if board_id_notes_content else ""


            # Construct the final description
            description_content = (
                f"{{code:java}}{self._jira_description_content}{{code}}"
                f"{scope} - {self.task_type} TryOut\n"
                "\n USB-Stick: -\n PD-Stick: -\n CD_DEF-Stick: -\n Map :- \n"
                f"{' '.join(self.part_details)}\n\n" # Join part details properly
                "{color:#ff0000}Work-A-Round for Production required{color}: No \n"
                f"{table_header}{table_rows}\n"
                f"\n*Note:*\n{full_board_note}\n"
                f"Checksums: https://hi-dms.de.bosch.com/docushare/dsweb/View/Collection-{str(self.collection_id).replace('.0', '')}"
            )

            # Construct customfield_10042 content
            customfield_10042_content = (
                f"h5.SW {self.task_sw}\n"
                f"{{code:java}}Used for {self.extracted_data1}{{code}}"
                f"{task_name_parts[0]} ({task_name_parts[1] if len(task_name_parts) > 1 else ''})"
                f"{{code:java}}PD Configuration {self.extracted_data2}{{code}}"
            )
            
            iss_upd.update(
                fields={
                    JIRA_SUMMARY_FIELD: summary,
                    JIRA_CUSTOM_FIELD_10042: customfield_10042_content,
                    JIRA_DESCRIPTION_FIELD: description_content
                }
            )

            print("\n" + "=" * 80 + "\n")
            print(f"Jira task {self.to_task_issue_id} is updated with SW {self.task_sw}")
            print("\n" + "=" * 80 + "\n")
            return True

        except JIRA.exceptions.JIRAError as e:
            print(f"JIRA Error updating issue {self.to_task_issue_id}: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during JIRA update: {e}")
            return False


if __name__ == "__main__":
    print(f"Create Tryout task Jira Version : {__version__}")
    creator = JiraIssueCreator()

    if not creator.read_input_excel():
        exit(1) # Exit if input file cannot be read

    if not creator.set_task_inputs():
        exit(1) # Exit if inputs cannot be set

    # Wrap these calls in checks as well for robustness
    creator.extract_jira_description()
    creator.read_tryout_mail_file()
    creator.read_image_overview()
    creator.update_jira_task()



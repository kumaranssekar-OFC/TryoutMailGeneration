import os
import glob
import numpy as np
import pandas as pd
import re
import math
import subprocess
import logging
from logging import handlers
import datetime
from jira import JIRA

# Assuming JiraAccess is a class that handles JIRA authentication and provides a JIRA object
from JiraAccess import jira_access
# Assuming ServerPath_File provides configuration like NeedToRun
import ServerPath_File as SPF

# Disable specific warnings if absolutely necessary, but address them if possible.
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

__version__ = "01.00"

# --- Console Color Setup ---
os.system('color') # Enables ANSI escape codes on Windows command prompt

# --- Logging Setup ---
LOG_FILENAME = "create_jira.log"
LOG_FORMAT = '%(asctime)s, %(levelname)s, %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configure logging before any log calls
log_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# File handler for rotating logs
file_handler = handlers.TimedRotatingFileHandler(
    filename=LOG_FILENAME, when='M', interval=1, backupCount=4, encoding="UTF-8"
)
file_handler.setFormatter(log_formatter)

# Get the root logger and add handlers
logger = logging.getLogger()
logger.setLevel(logging.INFO) # Overall logging level
logger.addHandler(file_handler)
# If you want console output during execution, uncomment the StreamHandler below:
# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(log_formatter)
# logger.addHandler(stream_handler)


# --- Constants ---
# File names
JIRA_RAW_DESCRIPTION_FILE = "jira_raw_description.txt"
JIRA_EXTRACTED_DETAILS_FILE = "jira_extracted_details.txt"
TRYOUT_MAIL_FILE_SUFFIX = ".txt"

# Image overview paths
IMAGE_OVERVIEW_BASE_PATH = r"\\bosch.com\dfsrb\DfsDE\DIV\CM\AI\SW_Releases\Nissan"
SERVER_LOCATIONS = ["0046", "0047", "0048", "0049"]

# JIRA field names and custom field IDs
JIRA_SUMMARY_FIELD = 'summary'
JIRA_CUSTOM_FIELD_10042 = 'customfield_10042'
JIRA_DESCRIPTION_FIELD = 'description'
JIRA_TASK_NAME_PREFIX = "h3. {color:#FF0080}" # Common prefix in JIRA descriptions
JIRA_TASK_NAME_COLOR_STRIP_PATTERN = r"h3\. \{color:.*?\}|\{color\}"

# Perl script names
FETCH_FCID_SCRIPT = "Fetch_from_FCID.pl"
TRYOUT_DEVICES_SCRIPT = "tryout_devices.pl"

# JIRA table definitions based on scope keywords
JIRA_TABLE_DEFINITIONS = {
    "A-IVI2": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6, "has_hyperflash": True},
    "CCS": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6, "has_hyperflash": True},
    "CCS1.1": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6, "has_hyperflash": True},
    "CCS 1.5": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6, "has_hyperflash": True},
    "P-IVI2": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6, "has_hyperflash": True},
    "PIVI2": {"header": "||HW||BoardID||Hyperflash Image||eMMC Image(s)||GNSS / CPLD||SW; Remarks||\n", "cols": 6, "has_hyperflash": True},
    "P-IVI": {"header": "||HW||BoardID||Image||owned by||SW; Remarks||\n", "cols": 5, "has_hyperflash": False},
    "DEFAULT": {"header": "||HW||BoardID||Image||owned by||SW; Remarks||\n", "cols": 5, "has_hyperflash": False} # Fallback
}

# Hyperflash mapping for A-IVI2 / CCS boards
HYPERFLASH_MAPPING = {
    "030D11": ["CPLD_PEXT_SBR_PM02", "flash_image_nissan-aivi2-c3-3gb.bin"],
    "030E11": ["CPLD_PEXT_SBR_PM02", "flash_image_nissan-aivi2-c3.bin"],
    "031311": ["CPLD_PEXT_SBR_M3_J32V_PM01", "flash_image_nissan-aivi2-j32v-c0.bin"],
    "031511": ["CPLD_PEXT_SBR_LATTICE_PM02", "flash_image_nissan-aivi2-c3-cpld.bin"],
    "031811": ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-b.bin"],
    "031611": ["CPLD_PEXT_SBR_M3_CCS11_PM01", "flash_image_nissan-aivi2-ccs11-b.bin"],
    "031411": ["CPLD_PEXT_SBR_LATTICE_PM02", "flash_image_nissan-aivi2-c3-3gb-cpld.bin"],
    "031711": ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-b-3gb.bin"],
    "030F11": ["CPLD_PEXT_SBR_M3_CCS11_PM01","flash_image_nissan-aivi2-b-3gb.bin"],
    "031111": ["CPLD_PEXT_SBR_M3_J32V_PM01","flash_image_nissan-aivi2-b-3gb.bin"],
    "031E11": ["CPLD_PEXT_SBR_PM02","flash_image_nissan-aivi2-c3-nd.bin"],
    "031D11": ["CPLD_PEXT_SBR_PM02","flash_image_nissan-aivi2-c3-3gb-nd.bin"],
    "032311": ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-c3-3gb-cpld-nd.bin"],
    "031911": ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-b-3gb-nd.bin"],
    "031C11": ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-b-3gb-nd.bin"],
    "031A11": ["CPLD_PEXT_SBR_LATTICE_PM02","flash_image_nissan-aivi2-b-nd.bin"],
}

# --- Global Configuration (from ServerPath_File) ---
# Assuming NeedToRun is a global flag for external script execution
# Standardize to upper for consistent comparison. Default to 'N' if not explicitly 'Y' or 'YES'.
NEED_TO_RUN_EXTERNAL_SCRIPTS = SPF.PathFormation.NeedToRun.upper() if hasattr(SPF.PathFormation, 'NeedToRun') else 'N'
if NEED_TO_RUN_EXTERNAL_SCRIPTS not in ['Y', 'YES']:
    NEED_TO_RUN_EXTERNAL_SCRIPTS = 'N'


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
        self.part_numbers = []         # Successor PNs
        self.pre_part_numbers = []     # Predecessor PNs
        self._num_part_numbers = 0
        self._num_pre_part_numbers = 0
        self.collection_id = None
        self.base_sw_versions = []     # Base SW names from Excel
        self.fcid_version = None
        self.to_hw_list = None

        # Data extracted from various sources
        self._jira_raw_description_content = ""
        self.extracted_jira_description_details = "" # Processed "Devices" section content
        self.tryout_mail_sw_id_tag_paths = ""
        self.tryout_mail_project_info = ""
        self.tryout_mail_pd_cd_config = {"PD Configuration": "", "CD Configuration": ""}

        self.processed_emmc_data = {} # {pn: [{emmc: "emmc_val", type: "direct"|"use"}, ...], ...}
        self.processed_map_data = {}  # {pn: {map_cut: "val", map_version: "val"}, ...}
        self.sw_stamps = []           # List of unique SW stamps found
        self.gnss_values = {}         # {pn: "GNSS_val", ...}
        self.sister_devices = {}      # {pn: "SisterDevice_val", ...}
        self.jira_client = None       # JIRA client instance


    def _get_jira_client(self):
        """Initializes and returns the JIRA client, ensuring only one instance is created."""
        if self.jira_client is None:
            try:
                self.jira_client = jira_access() # Assuming this returns a JIRA object
                logger.info("JIRA client initialized successfully.")
            except Exception as e:
                logger.critical(f"Failed to initialize JIRA client: {e}")
                raise
        return self.jira_client

    def read_input_excel(self, file_path="init.xlsx", sheet_name="ValidSheet"):
        """Reads input data from an Excel file."""
        try:
            self.df_init = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Successfully read input Excel file: {file_path}")
            return True
        except FileNotFoundError:
            logger.critical(f"Error: Input Excel file '{file_path}' not found.")
            return False
        except Exception as e:
            logger.critical(f"Error reading Excel file '{file_path}': {e}")
            return False

    def load_task_data_from_excel(self):
        """Extracts and sets task-related attributes from the initialized DataFrame."""
        if self.df_init is None:
            logger.critical("Error: Input data not loaded. Call read_input_excel first.")
            return False

        try:
            # Use .iloc[0] for single row access, and .astype(str) to handle mixed types gracefully.
            self.task_issue_id = str(self.df_init['Jira_Main_Task '].iloc[0]).strip()
            self.to_task_issue_id = str(self.df_init['Jira_TO_Task'].iloc[0]).strip()
            self.task_name = str(self.df_init['Task_Name'].iloc[0]).strip()
            self.task_type = str(self.df_init['Release_Type'].iloc[0]).strip()
            self.task_sw = str(self.df_init['SW_Version'].iloc[0]).strip()

            # Ensure lists, handle NaNs, convert to string
            self.part_numbers = self.df_init['Part_Numbers'].dropna().astype(str).tolist()
            self.pre_part_numbers = self.df_init['Predecessor_PN'].dropna().astype(str).tolist()
            self.base_sw_versions = self.df_init['Base_SW'].dropna().astype(str).tolist()

            self._num_part_numbers = len(self.part_numbers)
            self._num_pre_part_numbers = len(self.pre_part_numbers)

            self.collection_id = str(self.df_init['Docushare_CollectionID'].iloc[0]).strip()
            self.fcid_version = str(self.df_init['FCID_Version'].iloc[0]).strip()
            self.to_hw_list = str(self.df_init['HW_List'].iloc[0]).strip()

            logger.info(f"Task inputs loaded: Type='{self.task_type}', SW='{self.task_sw}', Part Numbers={self.part_numbers}, Predecessor PNs={self.pre_part_numbers}")
            return True
        except KeyError as e:
            logger.critical(f"Error: Missing expected column in Excel file: {e}")
            return False
        except IndexError:
            logger.critical("Error: Input Excel sheet is empty or does not contain enough rows.")
            return False
        except Exception as e:
            logger.critical(f"Error loading task data from Excel: {e}")
            return False

    def _clean_jira_task_name(self, name_to_clean):
        """Removes JIRA formatting and normalizes task name for comparison."""
        cleaned_name = re.sub(JIRA_TASK_NAME_COLOR_STRIP_PATTERN, "", name_to_clean).strip()
        return cleaned_name.lower().replace("re-flash", "reflash")

    def _fetch_jira_description(self):
        """Fetches the main JIRA task description and saves it to a temporary file."""
        jira_client = self._get_jira_client()
        try:
            main_issue = jira_client.issue(self.task_issue_id)
            description = main_issue.fields.description

            if not description:
                logger.warning(f"No description found for JIRA issue {self.task_issue_id}")
                return False

            # Replace JIRA newlines with standard newlines for easier parsing
            self._jira_raw_description_content = description.replace(r'\n', '\n')

            with open(JIRA_RAW_DESCRIPTION_FILE, "w", encoding="utf-8") as f_desc:
                f_desc.write(self._jira_raw_description_content)

            logger.info(f"Successfully fetched JIRA description for {self.task_issue_id}.")
            return True
        except JIRA.exceptions.JIRAError as e:
            logger.critical(f"JIRA Error accessing issue {self.task_issue_id}: {e}")
            return False
        except AttributeError:
            logger.critical(f"JIRA issue {self.task_issue_id} not found or has no description field.")
            return False
        except Exception as e:
            logger.critical(f"Error fetching JIRA description: {e}")
            return False

    def _find_matching_task_sections(self):
        """
        Scans the raw JIRA description file to find all sections matching the task name
        and filters based on task type (SplUpd/Image) and reflash status.
        Returns a list of (line_index, raw_line_content) tuples.
        """
        matching_sections = []
        target_task_name_cleaned = self._clean_jira_task_name(self.task_name)
        reflash_expected_for_type = (self.task_type == "SplUpd") # True if SplUpd, False if Image

        lines = self._jira_raw_description_content.splitlines()

        for i, line in enumerate(lines):
            # We are looking for lines that start a new task section (e.g., h3. {color:#FF0080}Task Name)
            if line.strip().startswith(JIRA_TASK_NAME_PREFIX.split('{color:')[0].strip()): # Check for "h3."
                cleaned_line_content = self._clean_jira_task_name(line)

                # Check for task name and SW version in proximity
                if target_task_name_cleaned in cleaned_line_content:
                    sw_found_near_task = False
                    for j in range(i, min(i + 5, len(lines))): # Check current and next 4 lines
                        if self.task_sw in lines[j]:
                            sw_found_near_task = True
                            break

                    if sw_found_near_task:
                        is_reflash_in_line = ("reflash" in cleaned_line_content)

                        if reflash_expected_for_type == is_reflash_in_line:
                            matching_sections.append((i, line))
                            logger.debug(f"Found matching task section: Line {i}, Content: {line}")
        return matching_sections

    def _select_task_section(self, matching_sections):
        """
        If multiple matching task sections are found, prompts the user to select one.
        Returns the (line_index, raw_line_content) of the selected section.
        """
        if not matching_sections:
            logger.error("No matching task sections found in JIRA description.")
            return None

        if len(matching_sections) == 1:
            line_index, line_content = matching_sections[0]
            cleaned_name = self._clean_jira_task_name(line_content)
            print(f"\n Only one task found, automatically selected: \033[94m{cleaned_name}\033[00m")
            logger.info(f"Automatically selected task section at line {line_index}: {line_content}")
            return line_index, line_content
        else:
            print("\n --- Multiple tasks found in JIRA description ---")
            for idx, (line_index, line_content) in enumerate(matching_sections):
                cleaned_name = self._clean_jira_task_name(line_content)
                print(f"\n \033[93m{idx}\033[00m - \033[92m{cleaned_name}\033[00m")
            try:
                selection = int(input("\n Please enter the index number of the desired task: "))
                if not (0 <= selection < len(matching_sections)):
                    raise ValueError("Invalid index selected.")
                selected_line_index, selected_line_content = matching_sections[selection]
                logger.info(f"User selected task section at line {selected_line_index}: {selected_line_content}")
                return selected_line_index, selected_line_content
            except ValueError as e:
                logger.critical(f"Invalid selection: {e}. Exiting.")
                return None
            except Exception as e:
                logger.critical(f"Error during task selection: {e}. Exiting.")
                return None

    def _parse_jira_task_details(self, start_line_index):
        """
        Parses the JIRA description starting from the selected task section to extract
        the "Devices" section content.
        """
        lines = self._jira_raw_description_content.splitlines()
        dev_expected_marker = "Devices"
        extracted_detail_lines = []

        # Find SW version line after the task section start
        sw_line_idx = -1
        for i in range(start_line_index, len(lines)):
            if self.task_sw in lines[i]:
                sw_line_idx = i
                logger.debug(f"SW '{self.task_sw}' found at line {sw_line_idx}.")
                break
        if sw_line_idx == -1:
            logger.warning(f"SW version '{self.task_sw}' not found after task name in description.")
            return []

        # Find "Devices" marker after SW version
        devices_marker_idx = -1
        for i in range(sw_line_idx, len(lines)):
            if dev_expected_marker in lines[i]:
                devices_marker_idx = i
                logger.debug(f"'Devices' marker found at line {devices_marker_idx}.")
                break
        if devices_marker_idx == -1:
            logger.warning(f"'{dev_expected_marker}' section not found after SW version in description.")
            return []

        # Start extracting lines after the "Devices" header (typically 1 or 2 lines after the marker)
        start_data_idx = devices_marker_idx + 1 # Adjusted from original +2 to capture more flexibly

        target_part_numbers = self.pre_part_numbers if self.task_type == "SplUpd" else self.part_numbers
        
        # This part requires a very specific format.
        # Iterating through all lines after 'Devices' and picking ones that match target PNs
        for i in range(start_data_idx, len(lines)):
            current_line = lines[i]
            # Stop if we hit another header or end of section
            if current_line.strip().startswith("h3.") or not current_line.strip():
                break

            for pn_to_match in target_part_numbers:
                if pn_to_match in current_line:
                    extracted_detail_lines.append(current_line)
                    break # Move to next line in description once a PN is matched
        
        return extracted_detail_lines

    def extract_jira_description(self):
        """
        Orchestrates the extraction of the relevant "Devices" section from the JIRA description.
        """
        if not self._fetch_jira_description():
            return False

        matching_sections = self._find_matching_task_sections()
        selected_section_info = self._select_task_section(matching_sections)

        if selected_section_info is None:
            logger.critical("No valid task section selected. Aborting JIRA description extraction.")
            return False

        selected_line_index, _ = selected_section_info
        raw_extracted_details = self._parse_jira_task_details(selected_line_index)

        if not raw_extracted_details:
            logger.warning("No device details found in the selected JIRA description section.")
            return False

        # Clean and store the extracted details
        cleaned_details = []
        for line in raw_extracted_details:
            # Replaced complex string replacements with a more general approach
            cleaned_line = line.replace("|", " ").replace("(/)", "").replace("(-)", "").replace("(x)", "").replace("(!)", "").replace("*", "").strip()
            if cleaned_line:
                cleaned_details.append(cleaned_line)

        self.extracted_jira_description_details = "\n".join(cleaned_details)
        with open(JIRA_EXTRACTED_DETAILS_FILE, "w", encoding="utf-8") as f:
            f.write(self.extracted_jira_description_details)
        
        logger.info(f"Successfully extracted JIRA description details for task '{self.task_name}'.")
        return True

    def _parse_tryout_mail_sections(self, content):
        """Parses the tryout mail content into specific sections."""
        sw_id_tag_lines = []
        paths_lines = []
        project_info = ""
        pd_config = ""
        cd_config = ""

        lines = content.splitlines()
        
        # Extract SW-ID and TAG
        for line in lines:
            if "SW-ID" in line or "TAG" in line:
                sw_id_tag_lines.append(line.strip())
        
        # Extract paths and project info
        paths_start_idx = -1
        project_start_idx = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith(r"\\bosch.com") and paths_start_idx == -1:
                paths_start_idx = i
            if r"\ADR3" in line and project_start_idx == -1:
                project_start_idx = i
        
        if paths_start_idx != -1 and project_start_idx != -1 and paths_start_idx < project_start_idx:
            for i in range(paths_start_idx, project_start_idx):
                if lines[i].strip():
                    paths_lines.append(lines[i].strip())
            project_info = lines[project_start_idx].replace(r"\ADR3", "").strip()

        # Combine SW-ID, TAG, and paths
        self.tryout_mail_sw_id_tag_paths = "\n".join(sw_id_tag_lines + paths_lines)

        # Extract PD Configuration
        pd_config_match = re.search(r"PD Configuration\s*(.*?)(?=\nCD Configuration|\n(?=\S)|$)", content, re.DOTALL)
        if pd_config_match:
            pd_config = pd_config_match.group(1).strip()
            
        cd_config_match = re.search(r"CD Configuration\s*(.*?)(?=\n(?=\S)|$)", content, re.DOTALL)
        if cd_config_match:
            cd_config = cd_config_match.group(1).strip()
        
        self.tryout_mail_project_info = project_info
        self.tryout_mail_pd_cd_config["PD Configuration"] = pd_config
        self.tryout_mail_pd_cd_config["CD Configuration"] = cd_config

    def read_tryout_mail_file(self):
        """
        Reads content from a tryout mail file (named after SW version)
        and extracts specific data sections.
        """
        tryout_mail_file_path = f"{self.task_sw}{TRYOUT_MAIL_FILE_SUFFIX}"
        try:
            with open(tryout_mail_file_path, 'r', encoding="utf-8") as f_mail:
                content = f_mail.read()
            self._parse_tryout_mail_sections(content)
            logger.info(f"Successfully read and parsed tryout mail file: {tryout_mail_file_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Tryout mail file '{tryout_mail_file_path}' not found. "
                           "SUB-Input section in JIRA Task will not be fully updated.")
            return False
        except Exception as e:
            logger.error(f"Error reading or parsing tryout mail file '{tryout_mail_file_path}': {e}")
            return False

    def _execute_perl_script(self, script_name, *args):
        """Helper to execute a perl script and capture its output."""
        cmd = ["perl", script_name, *args]
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=True, encoding="utf-8")
            logger.debug(f"Perl script '{script_name}' STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Perl script '{script_name}' STDERR:\n{result.stderr}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Perl script '{script_name}' failed with return code {e.returncode}. STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
            raise
        except FileNotFoundError:
            logger.critical(f"Perl interpreter or script '{script_name}' not found. "
                            "Make sure Perl is installed and in PATH, and scripts are accessible.")
            raise

    def _get_fcid_device_info(self, part_number):
        """Fetches Board_ID and GNSS value for a part number using Fetch_from_FCID.pl."""
        if any(scope in self.task_name for scope in ["A-IVI2", "CCS", "P-IVI2", "PIVI2"]):
            try:
                output = self._execute_perl_script(
                    FETCH_FCID_SCRIPT,
                    "-fcid", f"SWUPD_Tooling_{self.fcid_version}.xlsx",
                    "-p", part_number
                )
                board_id_match = re.search(r'Board_ID\s*=\s*(\S+?)(?:\s*\(|$)', output) # captures up to space or '('
                gnss_match = re.search(r'GNSS\s*=\s*(\w+)', output)

                board_id = board_id_match.group(1).strip() if board_id_match else "UNKNOWN_BOARD_ID"
                gnss = gnss_match.group(1).strip() if gnss_match else ""
                logger.info(f"Fetched FCID info for {part_number}: BoardID={board_id}, GNSS={gnss}")
                return board_id, gnss
            except Exception as e:
                logger.warning(f"Failed to fetch Board_ID/GNSS for {part_number} via FCID: {e}")
                return "UNKNOWN_BOARD_ID", ""
        return "UNKNOWN_BOARD_ID", ""

    def _get_sister_device_info(self, part_number):
        """Fetches sister device information for a part number using tryout_devices.pl."""
        if NEED_TO_RUN_EXTERNAL_SCRIPTS != "Y":
            return "<<Manually add Sister Device>>"

        try:
            output = self._execute_perl_script(
                TRYOUT_DEVICES_SCRIPT,
                "-fcid", f"SWUPD_Tooling_{self.fcid_version}.xlsx",
                "-hwlist", self.to_hw_list,
                "-p", part_number
            )
            sister_devices_matches = re.findall(r'\|\^\_([^"]*)\_\^\|', output)
            if sister_devices_matches:
                sister_device_str = ", ".join(sister_devices_matches)
                logger.info(f"Sister device found for {part_number}: {sister_device_str}")
                return sister_device_str
            else:
                logger.info(f"No sister device found for {part_number}.")
                return "No sister device found."
        except Exception as e:
            logger.warning(f"Failed to fetch sister device for {part_number}: {e}")
            return "Failed to retrieve sister device."

    def _get_image_overview_filepath(self, sw_name, location):
        """Resolves the full path to the images_overview_*.txt file."""
        sw_path_base = os.path.join(IMAGE_OVERVIEW_BASE_PATH, f"{location}_RN_AIVI_7513750800", "00_SW", "_Versions", sw_name, "IMX6")
        
        if not os.path.exists(sw_path_base):
            logger.debug(f"SW path base not found for {sw_name} at {location}: {sw_path_base}")
            return None, None

        sw_stamp_files = glob.glob(os.path.join(sw_path_base, "*.lnk"))
        if not sw_stamp_files:
            logger.debug(f"No .lnk file found for SW stamp at {sw_path_base}")
            return None, None

        sw_stamp = os.path.splitext(os.path.basename(sw_stamp_files[0]))[0]
        self.sw_stamps.append(sw_stamp) # Store for later use

        image_resides_path = os.path.join(IMAGE_OVERVIEW_BASE_PATH, f"{location}_RN_AIVI_7513750800", "00_SW", "Production", sw_stamp, "Release")
        
        if not os.path.exists(image_resides_path):
            logger.debug(f"Image resides path not found for {sw_name} stamp {sw_stamp} at {location}: {image_resides_path}")
            return None, None

        image_file_pattern = f"images_overview_{sw_name[:4]}.txt"
        image_files = glob.glob(os.path.join(image_resides_path, image_file_pattern))
        
        if not image_files:
            logger.debug(f"Image overview file '{image_file_pattern}' not found at {image_resides_path}")
            return None, None

        return sw_stamp, image_files[0]

    def _parse_image_overview_line(self, line, search_part_number):
        """
        Parses a single line from an image overview file to extract EMMC, map cut, and map version.
        Returns a dictionary or None if parsing fails.
        """
        line = line.strip()
        if not line or not search_part_number:
            return None

        # Look for direct match for "PN: " or "PN "
        if not (line.startswith(f"{search_part_number}:") or line.startswith(f"{search_part_number} ")):
            logger.debug(f"Line does not start with target part number '{search_part_number}': {line}")
            return None

        emmc_val, map_cut_val, map_version_val = "N/A", "N/A", "N/A"
        
        split_line = line.split()

        try:
            # Find EMMC value
            emmc_match = re.search(r'(emmc\S*)', line)
            if emmc_match:
                emmc_val = emmc_match.group(1)

            # Find PARTITION_SCHEM and subsequent map info
            map_schem_idx = -1
            for i, token in enumerate(split_line):
                if "PARTITION_SCHEM" in token:
                    map_schem_idx = i
                    break
            
            if map_schem_idx != -1 and map_schem_idx + 2 < len(split_line):
                map_cut_val = split_line[map_schem_idx + 1]
                map_version_val = split_line[map_schem_idx + 2].replace(",", "")
            elif map_schem_idx != -1 and map_schem_idx + 1 < len(split_line): # Fallback if only map_cut
                map_cut_val = split_line[map_schem_idx + 1]

        except IndexError as ie:
            logger.warning(f"Index error parsing image overview line for '{search_part_number}': {line}. Error: {ie}")
            return None
        except Exception as e:
            logger.warning(f"General error parsing image overview line for '{search_part_number}': {line}. Error: {e}")
            return None

        return {"emmc": emmc_val, "map_cut": map_cut_val, "map_version": map_version_val}


    def _process_part_number_in_image_overview(self, image_file_path, part_number, base_sw_name, is_splupd, display_pn=None):
        """
        Processes a single part number from the image overview file, handling direct entries and reuse logic.
        """
        if not os.path.exists(image_file_path):
            logger.warning(f"Image overview file not found for {part_number}: {image_file_path}")
            return False

        logger.info(f"Processing image overview for PN '{part_number}' (Base SW: '{base_sw_name}') from '{image_file_path}'")

        # Fetch FCID and Sister Device info once per PN
        board_id, gnss = self._get_fcid_device_info(part_number)
        sister_device = self._get_sister_device_info(part_number)
        
        self.gnss_values[part_number] = gnss
        self.sister_devices[part_number] = sister_device

        with open(image_file_path, "r", encoding="utf-8") as f_iot:
            iot_lines = f_iot.readlines()

        direct_entry_found = False
        parsed_data = {} # Stores data for current part number

        # --- First Pass: Find Direct Entry for the Part Number ---
        for i, line in enumerate(iot_lines):
            line_stripped = line.strip()
            # Direct entry should start with the part number and not be a "-> use" line
            if (line_stripped.startswith(f"{part_number}:") or line_stripped.startswith(f"{part_number} ")) \
               and "-> use" not in line_stripped:
                
                parsed_details = self._parse_image_overview_line(line_stripped, part_number)
                if parsed_details:
                    parsed_data = parsed_details
                    parsed_data["board_id"] = board_id # Add board_id to parsed data
                    
                    self.processed_map_data[part_number] = {
                        "map_cut": parsed_data["map_cut"],
                        "map_version": parsed_data["map_version"]
                    }
                    if part_number not in self.processed_emmc_data:
                        self.processed_emmc_data[part_number] = []
                    self.processed_emmc_data[part_number].append({"emmc": parsed_data["emmc"], "type": "direct"})
                    direct_entry_found = True
                    logger.debug(f"Direct entry found for {part_number}: {parsed_data}")
                    break # Found the primary entry, proceed to check for reuse

        if not direct_entry_found:
            logger.warning(f"No direct image overview entry found for part number: {part_number}")
            return False

        # --- Second Pass: Check for Reuse Entries ---
        # If a direct entry was found, check if it reuses another EMMC
        for i, line in enumerate(iot_lines):
            line_stripped = line.strip()
            reuse_match = re.search(r'-> use\s*(\S+)', line_stripped)
            if reuse_match and reuse_match.group(1) == part_number:
                # This line means 'part_number' reuses another PN's EMMC.
                # However, the previous logic was about part_number reusing a *different* PN's EMMC.
                # The regex `pattern = "\d.+\d+(\w+)"` in your original suggests extracting the reused PN ID.
                # Let's assume `line` contains something like "SOME_PN -> use 030E11" and `part_number` is "030E11".
                # The actual intent of the reuse logic is a bit ambiguous.
                # Re-interpreting: If the current `part_number` is listed as a *reused* item for another PN,
                # or if `part_number` needs to find what it *re-uses*.

                # Original logic: If current line is "-> use", and it uses current `part_number`
                # (which means current PN is a reused PN, not the reuser)
                reused_pn_id = reuse_match.group(1)
                if reused_pn_id == part_number:
                    # This means 'part_number' is a target of reuse.
                    # The value extracted was the direct entry. We've done that.
                    # The original `check_reusage` loop was trying to find a line like "A -> use B", where A is current PN.
                    # This means current PN (A) reuses B. So we need to find B's EMMC.

                    # Let's find the EMMC for the *reused* part number.
                    # The logic here in the original was highly nested and hard to follow.
                    # Assuming a line like "030F11: SBR_NISSAN_C3.img (PARTITION_SCHEM 2GB 001) -> use 030E11"
                    # If `part_number` is "030F11", then it 'uses' "030E11".
                    # We need to find the EMMC for "030E11".

                    # Simplified approach for "A -> use B"
                    # If part_number (A) reuses `reused_target_pn_id` (B)
                    
                    if not line_stripped.startswith(f"{part_number}:"): # Only process reuse line if it's for this PN as re-user
                        continue # This line is not directly about `part_number` as the one reusing
                    
                    reused_target_pn_id = re.search(r'-> use\s*(\S+)', line_stripped)
                    if not reused_target_pn_id:
                        continue # No valid reuse target.
                    
                    actual_reused_pn = reused_target_pn_id.group(1)

                    for j, check_line in enumerate(iot_lines):
                        check_line_stripped = check_line.strip()
                        if check_line_stripped.startswith(f"{actual_reused_pn}:") and "-> use" not in check_line_stripped:
                            reused_emmc_details = self._parse_image_overview_line(check_line_stripped, actual_reused_pn)
                            if reused_emmc_details:
                                if part_number not in self.processed_emmc_data:
                                    self.processed_emmc_data[part_number] = []
                                self.processed_emmc_data[part_number].append({"emmc": f"{{use:{reused_emmc_details['emmc']}}}", "type": "reuse"})
                                logger.debug(f"Reuse EMMC added for {part_number} from {actual_reused_pn}: {reused_emmc_details['emmc']}")
                            break # Found EMMC for the reused PN
                
        return True

    def _collect_all_image_data(self):
        """
        Orchestrates the reading and processing of image overview files
        for all part numbers based on task type.
        """
        self.processed_emmc_data = {}
        self.processed_map_data = {}
        self.sw_stamps = []
        self.gnss_values = {}
        self.sister_devices = {}

        part_to_sw_map = {} # Mapping for SplUpd
        for i, pn in enumerate(self.pre_part_numbers):
            if pd.notna(pn) and i < len(self.base_sw_versions):
                part_to_sw_map[pn] = self.base_sw_versions[i]

        processed_pns_in_session = set() # To prevent re-processing PNs within a single run

        if self.task_type == "SplUpd":
            target_pns = self.pre_part_numbers
            corresponding_pns = self.part_numbers # For display (successor PN)
        else: # Image or other types
            target_pns = self.part_numbers
            corresponding_pns = self.pre_part_numbers # For display (predecessor PN)

        for i, current_pn in enumerate(target_pns):
            if pd.isna(current_pn) or current_pn in processed_pns_in_session:
                continue

            sw_to_use = part_to_sw_map.get(current_pn) if self.task_type == "SplUpd" else self.task_sw
            if not sw_to_use:
                logger.warning(f"No SW version found for PN '{current_pn}'. Skipping image overview processing.")
                continue

            found_in_any_location = False
            for location in SERVER_LOCATIONS:
                sw_stamp, image_file_path = self._get_image_overview_filepath(sw_to_use, location)
                if image_file_path:
                    display_pn = corresponding_pns[i] if i < len(corresponding_pns) else None
                    if self._process_part_number_in_image_overview(image_file_path, current_pn, sw_to_use, self.task_type == "SplUpd", display_pn):
                        found_in_any_location = True
                        processed_pns_in_session.add(current_pn)
                        break # Found for this PN, move to next
            
            if not found_in_any_location:
                logger.warning(f"Could not find image overview data for PN '{current_pn}' across all server locations.")

        # Ensure unique SW stamps (glob.glob can return duplicates)
        self.sw_stamps = list(dict.fromkeys(self.sw_stamps))

        logger.info(f"Image data collection complete. PNs processed: {processed_pns_in_session}")


    def read_image_overview(self):
        """Public method to trigger image overview data collection."""
        self._collect_all_image_data()


    def _determine_dev_prd(self):
        """Determines if the task is DEV or PRD based on TSB/DSB in task name."""
        task_name_upper = self.task_name.upper()
        if "TSB" in task_name_upper or "DSB" in task_name_upper:
            return "DEV"
        return "PRD"

    def _get_jira_table_metadata(self):
        """Returns the JIRA table header, column count, and hyperflash status based on task name keywords."""
        for keyword, definition in JIRA_TABLE_DEFINITIONS.items():
            if keyword in self.task_name:
                return definition
        return JIRA_TABLE_DEFINITIONS["DEFAULT"]

    def _prepare_jira_table_data(self):
        """
        Consolidates all collected data into a structured list of dictionaries,
        ready for JIRA table row construction.
        """
        table_rows_data = []

        # Iterate over successor part numbers (self.part_numbers) to build the table
        # For SplUpd, the `part_numbers` are the successors, and `pre_part_numbers` are the actual PNs to look up data for.
        # For other types, `part_numbers` are the actual PNs.

        for i, display_pn in enumerate(self.part_numbers):
            actual_lookup_pn = self.pre_part_numbers[i] if self.task_type == "SplUpd" and i < len(self.pre_part_numbers) else display_pn
            if pd.isna(actual_lookup_pn):
                logger.warning(f"Skipping table data for display PN '{display_pn}' due to missing actual lookup PN.")
                continue

            emmc_entries = self.processed_emmc_data.get(actual_lookup_pn, [])
            map_details = self.processed_map_data.get(actual_lookup_pn, {"map_cut": "N/A", "map_version": "N/A"})
            gnss_val = self.gnss_values.get(actual_lookup_pn, "N/A")
            sister_dev_val = self.sister_devices.get(actual_lookup_pn, "Not known")

            # Combine EMMC entries into a single string
            emmc_images_str = ", ".join([entry["emmc"] for entry in emmc_entries]) if emmc_entries else "N/A"
            
            # Determine BoardID from the first EMMC image (heuristic)
            board_id_match = re.search(r'(\w{6})', emmc_images_str) # Looks for 6 alphanumeric chars
            board_id = board_id_match.group(1) if board_id_match else "UNKNOWN_BOARD_ID"
            
            # Get base SW name for remarks (handles both SplUpd and other types)
            sw_for_remarks = self.base_sw_versions[i].split('_')[0] if self.task_type == "SplUpd" and i < len(self.base_sw_versions) else self.task_sw.split('_')[0]

            table_rows_data.append({
                "display_pn": display_pn,
                "lookup_pn": actual_lookup_pn,
                "board_id": board_id,
                "emmc_images": emmc_images_str,
                "map_cut": map_details["map_cut"],
                "map_version": map_details["map_version"],
                "gnss": gnss_val,
                "sister_device": sister_dev_val,
                "sw_for_remarks": sw_for_remarks
            })
        return table_rows_data

    def _build_jira_table_rows_and_notes(self, table_data, dev_prd, table_metadata):
        """Constructs the rows for the JIRA table and collects BoardID notes."""
        jira_table_rows_content = []
        board_id_notes_content = []
        
        # Determine the primary scope from task name to apply hyperflash logic
        primary_scope = "DEFAULT"
        for keyword in JIRA_TABLE_DEFINITIONS:
            if keyword in self.task_name:
                primary_scope = keyword
                break

        for row_data in table_data:
            display_pn = row_data["display_pn"]
            lookup_pn = row_data["lookup_pn"]
            board_id = row_data["board_id"]
            emmc_images = row_data["emmc_images"]
            gnss = row_data["gnss"]
            sister_device = row_data["sister_device"]
            sw_for_remarks = row_data["sw_for_remarks"]

            # Part number display in table
            part_number_display_str = f"*{display_pn}*"
            if display_pn != lookup_pn: # If it's a successor PN, show predecessor as well
                part_number_display_str += f" (Pred: {lookup_pn})"
            
            # Add sister device info below part number
            part_number_display_str += f"\\n *Sister Device:*\\n ({sister_device})"
            
            hyperflash_image = "N/A"
            cpld_gnss_info = gnss # Default to just GNSS
            
            if table_metadata.get("has_hyperflash") and board_id in HYPERFLASH_MAPPING:
                hf_info = HYPERFLASH_MAPPING[board_id]
                cpld_gnss_info = f"{gnss} / {hf_info[0]}"
                hyperflash_image = hf_info[1]
                board_id_notes_content.append(f"*{board_id}* : {hf_info[1]}")
            
            # Construct row based on number of columns
            if table_metadata["cols"] == 6: # Hyperflash scopes
                row_content = (
                    f"|{part_number_display_str} |{board_id} | {hyperflash_image} | {emmc_images}| {cpld_gnss_info} | "
                    f"SW_{sw_for_remarks}_{dev_prd}; \\n "
                    f"TryOut: (?)(?) \\n Config: (?) \\n CheckSums: (?) \\n DS: (?) \\n  |"
                )
            elif table_metadata["cols"] == 5: # P-IVI scope and DEFAULT
                row_content = (
                    f"|{part_number_display_str} |{board_id} | {emmc_images}|[~mkr2hi]| "
                    f"SW_{sw_for_remarks}_{dev_prd}; \\n "
                    f"TryOut: (?)(?) \\n Config: (?) \\n CheckSums: (?) \\n DS: (?) \\n  |"
                )
            else: # Fallback for unexpected column count
                logger.warning(f"Unexpected column count {table_metadata['cols']}. Using default 5-column format.")
                row_content = (
                    f"|{part_number_display_str} |{board_id} | {emmc_images}|[~mkr2hi]| "
                    f"SW_{sw_for_remarks}_{dev_prd}; \\n "
                    f"TryOut: (?)(?) \\n Config: (?) \\n CheckSums: (?) \\n DS: (?) \\n  |"
                )
            jira_table_rows_content.append(row_content)
        
        # Ensure unique board ID notes and join them
        unique_board_notes = "\n".join(sorted(list(set(board_id_notes_content))))
        return "\n".join(jira_table_rows_content), unique_board_notes

    def _format_jira_description(self, table_metadata, jira_table_rows_str, board_id_notes_str):
        """Assembles the final JIRA description string."""
        # Determine scope and Board Note prefix based on task name
        scope_for_desc = "A-IVI" # Default scope
        board_note_prefix = ""
        for keyword in JIRA_TABLE_DEFINITIONS:
            if keyword in self.task_name:
                scope_for_desc = keyword
                if table_metadata.get("has_hyperflash"):
                    board_note_prefix = "BoardID – Hyperflash file name assignment for the release to production \\n"
                break
        
        full_board_note_section = f"{board_note_prefix}{board_id_notes_str}" if board_id_notes_str else ""
        
        # Format USB-Stick path
        usb_stick_path = "{Please Update manually}"
        if self.task_type != "Device Conversion" and self.tryout_mail_sw_id_tag_paths:
            # Extract actual paths from tryout_mail_sw_id_tag_paths
            path_lines = [line.strip() for line in self.tryout_mail_sw_id_tag_paths.splitlines() if line.startswith(r"\\bosch.com")]
            if path_lines:
                usb_stick_path = "\\n".join(path_lines) # Join paths with JIRA newline
        
        # Map details for JIRA description
        map_details_list = []
        for pn_display in self.part_numbers:
            actual_pn = self.pre_part_numbers[i] if self.task_type == "SplUpd" and i < len(self.pre_part_numbers) else pn_display
            if pd.isna(actual_pn): continue

            map_info = self.processed_map_data.get(actual_pn, {"map_cut": "N/A", "map_version": "N/A"})
            if self.task_type == "SplUpd" and pn_display != actual_pn:
                map_details_list.append(f"{pn_display} (Pred : {actual_pn}) : {map_info['map_cut']} {map_info['map_version']}")
            else:
                map_details_list.append(f"{actual_pn} : {map_info['map_cut']} {map_info['map_version']}")

        map_details_str = "\\n".join([entry for entry in map_details_list if "No_Map ()" not in entry])
        
        # Compatibility Matrix for SplUpd
        compatibility_matrix_section = "*Compatibility Matrix:-* \\n" if self.task_type == "SplUpd" else ""

        description_content = (
            f"{{code:java}}{self.extracted_jira_description_details}{{code}}"
            f"{scope_for_desc} - {self.task_type} TryOut\\n"
            f"\\nUSB-Stick:\\n {usb_stick_path}\\n"
            "PD-Stick: -\\n"
            "CD_DEF-Stick: -\\n"
            f"Map :-\\n{map_details_str}\\n\\n"
            f"{compatibility_matrix_section}"
            "{color:#ff0000}Work-A-Round for Production required{color}: No \\n"
            f"{table_metadata['header']}{jira_table_rows_str}\\n"
            f"\\n*Note:*\\n{full_board_note_section}\\n"
            f"Checksums: https://hi-dms.de.bosch.com/docushare/dsweb/View/Collection-{str(self.collection_id).replace('.0', '')}"
        )
        return description_content

    def _format_jira_customfield_10042(self):
        """Assembles the content for JIRA customfield_10042."""
        task_name_parts = self.task_name.split()
        project_id_for_customfield = task_name_parts[0] if task_name_parts else ""
        project_version_for_customfield = task_name_parts[1] if len(task_name_parts) > 1 else ""

        customfield_content = (
            f"h5.SW {self.task_sw}\\n"
            f"{{code:java}}Used for {self.task_issue_id} {self.task_name}{{code}}"
            f"{project_id_for_customfield} ({project_version_for_customfield})"
            f"{{code:java}}Project: {self.tryout_mail_project_info}{{code}}" # Replaced with specific project info
            f"{{code:java}}PD Configuration    {self.tryout_mail_pd_cd_config['PD Configuration']}{{code}}"
            f"{{code:java}}CD Configuration    {self.tryout_mail_pd_cd_config['CD Configuration']}{{code}}"
        )
        return customfield_content

    def update_jira_task(self):
        """
        Constructs the JIRA description and custom fields, then updates the JIRA sub-task.
        """
        jira_client = self._get_jira_client()
        try:
            issue_to_update = jira_client.issue(self.to_task_issue_id)

            dev_prd_status = self._determine_dev_prd()
            table_metadata = self._get_jira_table_metadata()
            
            prepared_table_data = self._prepare_jira_table_data()
            jira_table_rows_str, board_id_notes_str = self._build_jira_table_rows_and_notes(
                prepared_table_data, dev_prd_status, table_metadata
            )

            # Determine JIRA summary
            summary_prefix = "Perform Reflash Try-Out" if self.task_type == "SplUpd" else "Perform Internal Try-Out"
            summary = f"{summary_prefix} with SW {self.task_sw} ({self.task_name})"

            description_payload = self._format_jira_description(
                table_metadata, jira_table_rows_str, board_id_notes_str
            )
            customfield_payload = self._format_jira_customfield_10042()
            
            issue_to_update.update(
                fields={
                    JIRA_SUMMARY_FIELD: summary,
                    JIRA_CUSTOM_FIELD_10042: customfield_payload,
                    JIRA_DESCRIPTION_FIELD: description_payload
                }
            )

            logger.info(f"Jira task {self.to_task_issue_id} updated successfully with SW {self.task_sw}")
            print("\n" + "=" * 80 + "\n")
            print(f"\n \033[95m  Jira task {self.to_task_issue_id} is updated with SW {self.task_sw} \033[00m \n")
            print("\n" + "=" * 80 + "\n")
            return True

        except JIRA.exceptions.JIRAError as e:
            logger.critical(f"JIRA Error updating issue {self.to_task_issue_id}: {e}")
            return False
        except Exception as e:
            logger.critical(f"An unexpected error occurred during JIRA update: {e}", exc_info=True)
            return False
    
    def cleanup_temp_files(self):
        """Removes temporary files created during execution."""
        files_to_remove = [
            JIRA_RAW_DESCRIPTION_FILE,
            JIRA_EXTRACTED_DETAILS_FILE,
            f"{self.task_sw}{TRYOUT_MAIL_FILE_SUFFIX}"
        ]
        for file_path in files_to_remove:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed temporary file: {file_path}")
                except OSError as e:
                    logger.warning(f"Error removing temporary file {file_path}: {e}")
            else:
                logger.debug(f"Temporary file not found: {file_path}")


if __name__ == "__main__":
    logger.info(f"Create Tryout task Jira Version : {__version__}")
    print(f"Create Tryout task Jira Version : {__version__}")

    creator = JiraIssueCreator()

    try:
        if not creator.read_input_excel():
            exit(1)

        if not creator.load_task_data_from_excel():
            exit(1)

        # Proceed with subsequent steps only if previous ones were successful
        if creator.extract_jira_description():
            creator.read_tryout_mail_file() # This may warn but not exit if file is optional
            creator.read_image_overview()
            creator.update_jira_task()
        else:
            logger.critical("Failed to extract JIRA description. Aborting update.")
            exit(1)

    except Exception as main_e:
        logger.critical(f"Unhandled exception in main execution: {main_e}", exc_info=True)
        print(f"\n\033[91mCRITICAL ERROR: An unhandled exception occurred. Check logs for details.\033[00m")
        exit(1)
    finally:
        creator.cleanup_temp_files()
        logger.info("Script execution finished.")
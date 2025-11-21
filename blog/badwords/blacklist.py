from django.conf import settings
import os

def read_file_to_list(file_path):
    """
    Reads a .txt file and returns a list of strings, one for each line.

    :param file_path: The full path to the text file.
    :return: A list of strings, with newline characters stripped.
    """
    lines_list = []
    try:
        # 1. Open the file using a 'with' statement for automatic closing
        # 'r' mode is for reading
        with open(file_path, 'r') as file:
            # 2. Use the readlines() method
            # This method reads all lines and returns them as a list of strings.
            lines_list = file.readlines()

        # 3. Process the list to strip newline characters (\n)
        # Using a list comprehension for efficiency and conciseness.
        stripped_lines = [line.strip().lower() for line in lines_list]

        return stripped_lines

    except FileNotFoundError:
        print(f"Error: The file was not found at {file_path}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


file_dir = os.path.dirname(__file__)

badwords = read_file_to_list(os.path.join(file_dir, "swearWords.txt"))
domains = read_file_to_list(os.path.join(file_dir, "domain_blacklist.txt"))
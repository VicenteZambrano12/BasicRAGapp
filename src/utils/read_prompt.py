def read_text_file(filepath):
  
  """
  Reads a text file and returns its content as a string.

  Args:
    filepath: The path to the text file.

  Returns:
    The content of the file as a string, or None if an error occurs.
  """
  try:
    with open(filepath, 'r', encoding='utf-8') as file:
      content = file.read()
      return content
  except FileNotFoundError:
    print(f"Error: File not found at {filepath}")
    return None
  except Exception as e:
    print(f"An error occurred: {e}")
    return None
import os

def extract_folder_and_subject(path: str):
    # Get the folder name (last directory before the file)
    folder_name = os.path.basename(os.path.dirname(path))
    
    # Get the filename without extension
    filename = os.path.splitext(os.path.basename(path))[0]
    
    # Remove the trailing "_<folder_name>" if it exists
    suffix = f"_{folder_name.lower()}"
    if filename.lower().endswith(suffix):
        subject = filename[:-len(suffix)]
    else:
        subject = filename  # fallback in case suffix not found
    
    return folder_name, subject

# Example usage
path = "/teamspace/studios/this_studio/My_first_ai_app/backend/docs/Extremadura/history_extremadura.pdf"
folder, subject = extract_folder_and_subject(path)

print("Folder:", folder)    # -> Extremadura
print("Subject:", subject)  # -> history
import os

# Define the directory
target_directory = "C:\\Users\\Vza 12\\Documents\\PAUHelper\\PAUHelper\\src\\prompts"

# The "Metaprompted" text in SPANISH
# Instructions: Input can be text/image. Never say you cannot see images.
text_to_insert = """
[SISTEMA: PROTOCOLOS DE VISIÓN Y ENTRADA]
La entrada puede ser texto o imagen. Eres un modelo multimodal.
Si se proporciona una imagen, analízala de inmediato.
NUNCA digas que no puedes ver, analizar o responder a imágenes.
"""

# Check if the directory exists
if not os.path.isdir(target_directory):
    print(f"Error: Directory '{target_directory}' not found.")
else:
    print(f"Processing files in '{target_directory}'...")
    
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    # 1. Read lines
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 2. Insert text at Index 1 (Between Line 1 and Line 2)
                    # We add a newline character to ensure spacing
                    formatted_insert = text_to_insert + "\n"
                    
                    if len(lines) >= 1:
                        lines.insert(1, formatted_insert)
                    else:
                        # If file is empty, just append it
                        lines.append(formatted_insert)
                    
                    # 3. Write changes back
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                        
                    print(f"Updated: {file_path}")

                except Exception as e:
                    print(f"Failed to update {file_path}: {e}")

    print("Insertion process completed.")
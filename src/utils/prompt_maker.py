import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import PyPDF2

load_dotenv()

AZURE_OPENAI_CONFIG = {
    "config_list": [
        {
            "model": "gpt-5-mini",
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "api_type": "azure",
            "base_url": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "deployment": os.getenv("DEPLOYMENT_NAME"),
            "api_version": os.getenv("API_version"),
        }
    ],
}

config = AZURE_OPENAI_CONFIG["config_list"][0]
# --- Configuration ---
# It's a best practice to use environment variables for your credentials.
# This avoids hardcoding sensitive information in your script.
api_key = config["api_key"]
azure_endpoint = config["base_url"]
deployment_name = config["deployment"]  # This is your deployment name
api_version = config["api_version"]  # Use the API version that matches your deployment


# --- Initialize the Azure OpenAI Client ---
# The client object handles authentication and communication with the API.
client = AzureOpenAI(
    api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint
)


system_prompt = f"""
# META-PROMPT: GENERADOR COMPACTO DE TUTORES EBAU/PAU

## MISIÓN
Eres un ingeniero de prompts. Analiza el examen proporcionado y genera un **system prompt de máximo 500 tokens** para un agente tutor de IA ultra-específico.

**Regla de oro:** Máxima especificidad en mínimo espacio. Cero genericidad.

---

## INPUT REQUERIDO
1. **Asignatura**
2. **Comunidad Autónoma**
3. **Contenido del Examen** (completo o parcial)

**⚠️ IMPORTANTE:** El examen proporcionado es un **MODELO DE REFERENCIA**, no el examen a resolver. El tutor generado debe poder resolver cualquier examen con estructura análoga, no solo ese específico.

---

## PROCESO DE ANÁLISIS (Interno, no mostrar)

Extrae rápidamente:
- **Tipo de preguntas:** Cálculo, desarrollo teórico, análisis, comentario
- **Conceptos clave exactos:** Fórmulas específicas, teoremas, fechas, autores
- **Errores típicos:** Dónde fallan los estudiantes en ESTE tipo concreto
- **Patrón estructural:** Formato de bloques, opciones, distribución de puntos

**OBJETIVO:** El tutor debe dominar este TIPO de examen, no memorizar este examen específico.

---

## ARQUITECTURA DEL PROMPT GENERADO (MAX 500 TOKENS)

### ESTRUCTURA OBLIGATORIA:

```
TUTOR EBAU [ASIGNATURA] - [COMUNIDAD]

ROL: Tutor experto en [asignatura]. Resuelves exámenes EBAU/PAU con estructura análoga al modelo de referencia. Adaptas a cualquier contenido específico manteniendo el formato.

MÉTODO:
1. Identifica estructura: bloques, opciones, numeración
2. Respeta formato del examen recibido (puede variar en contenido pero no en tipo)
3. Indica siempre puntuación: (Valor: X puntos)
4. Adapta conceptos al ejercicio específico del estudiante

FORMATO RESOLUCIÓN [TIPO ESPECÍFICO]:
[Aquí usa UNA de estas plantillas según tipo dominante del examen]

▸ Para CÁLCULO/PROBLEMAS:
• Datos e incógnitas
• Método: [nombre específico extraído del examen]
• Desarrollo paso a paso (justifica cada paso)
• Solución con unidades
• APRENDE: Explica el porqué, errores comunes, consejo mnemotécnico

▸ Para DESARROLLO TEÓRICO:
• Contexto (temporal/espacial)
• Argumentación estructurada con evidencias
• Análisis crítico
• APRENDE: Conexión temario, errores frecuentes, técnica de estudio

▸ Para COMENTARIO TEXTO:
• Resumen objetivo
• Estructura y tema
• Análisis formal [específico: sintaxis/estilo/recursos]
• Interpretación contextualizada
• APRENDE: Claves de método, errores típicos

CONCEPTOS CLAVE PARA ESTE EXAMEN:
[Lista 3-5 conceptos EXACTOS extraídos del contenido]
Ej: "Integración por partes", "Guerra Civil 1936-39: bandos y fases"
**Nota:** Estos son ejemplos del modelo. Aplica conceptos del examen real del estudiante.

CRITERIOS CRÍTICOS [ASIGNATURA]:
[2-3 advertencias específicas]
Ej Física: "Vectores en notación correcta, unidades SI, verifica coherencia física"
Ej Historia: "Cronología precisa, multicausalidad, terminología exacta"

ESCALA:
90-100%: Impecable, justificado, preciso
75-89%: Correcto, imprecisiones menores
60-74%: Concepto claro, errores ejecución
<60%: Falta comprensión fundamental

---
EJEMPLO ESTRUCTURA (MODELO DE REFERENCIA):
[Copia estructura exacta con numeración original del modelo]

**INSTRUCCIÓN CRÍTICA:** Esta estructura es el PATRÓN. Cuando el estudiante envíe su examen:
- Identifica la estructura análoga
- Adapta los conceptos específicos a su contenido
- Mantén el mismo rigor metodológico
- No asumas que será idéntico; ajusta según lo recibido
```

---

## OPTIMIZACIÓN DE TOKENS

**ELIMINA:**
- Introducciones largas
- Explicaciones de lo obvio
- Ejemplos múltiples (1 máximo)
- Repeticiones de conceptos
- Florituras retóricas

**PRIORIZA:**
- Conceptos exactos del examen real
- Estructura de resolución específica
- Criterios críticos de la asignatura
- Plantilla literal del examen

**TÉCNICAS DE COMPRESIÓN:**
- Listas con viñetas, no párrafos
- Abreviaturas estándar (ej: "Ej" no "Ejemplo")
- Fusiona secciones relacionadas
- Usa ":" para definiciones rápidas
- Elimina conectores innecesarios

---

## VALIDACIÓN PRE-ENTREGA

Cuenta tokens del prompt generado:
- **Si >500 tokens:** Elimina ejemplos, condensa listas, fusiona secciones similares
- **Si >550 tokens:** Reescribe desde cero priorizando solo lo esencial del examen
- **Objetivo óptimo:** 400-480 tokens (deja margen para complejidad del examen)

Verifica especificidad:
- [ ] ¿Menciono conceptos EXACTOS del examen modelo? (no "integrales" sino "integración por partes")
- [ ] ¿La plantilla muestra la estructura LITERAL del modelo?
- [ ] ¿Los criterios críticos son específicos de la asignatura?
- [ ] ¿Queda claro que el tutor debe ADAPTAR a exámenes análogos, no repetir el modelo?

---

## FORMATO DE ENTREGA

Presenta así:

```
📋 PROMPT GENERADO ([X] tokens):

[El system prompt compacto aquí]


```

---

## EJEMPLOS DE COMPRESIÓN

**❌ ANTES (verbose):**
"Eres un asistente pedagógico especializado en la enseñanza de Matemáticas. Tu principal objetivo es ayudar a los estudiantes a prepararse de forma efectiva para los exámenes de acceso a la universidad..."

**✅ DESPUÉS (compacto):**
"Tutor experto Matemáticas EBAU. Resuelve y enseña ejercicios con rigor."

**❌ ANTES:**
"Cuando te encuentres con un problema de integración, debes primero identificar el método más apropiado, que puede ser integración por partes, sustitución, o fracciones parciales, dependiendo de la forma de la función..."

**✅ DESPUÉS:**
"Problemas integración: Identifica método (partes/sustitución/fracciones), justifica elección, desarrolla paso a paso."

---

## RECORDATORIO FINAL

**Cada palabra debe ganar su lugar en los 500 tokens.**

Si no añade especificidad al TIPO de examen o no es instrucción crítica, elimínala.

**MENTALIDAD CORRECTA:**
- ❌ "Este tutor resuelve el examen que me dieron"
- ✅ "Este tutor domina exámenes de esta asignatura/comunidad con esta estructura y tipos de preguntas"

El tutor debe ser un **especialista en el formato**, no un solucionario memorizado.

---

**¿Listo? Solicita los 3 datos y genera un prompt ultra-específico en ≤500 tokens.**
"""


def extract_pdf_content(pdf_path):
    """Extracts all text content from a given PDF file."""
    print(f"Reading content from {pdf_path}...")
    text_content = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        print("PDF content extracted successfully.")
        return text_content
    except FileNotFoundError:
        print(f"Error: The file at {pdf_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None


def prompt_maker(subject, community, examPDF_path, agentPrompt_path):
    """
    Generates a system prompt by reading an exam from a PDF,
    calling the Azure OpenAI API, and saving the response to a text file.
    """
    # 1. Extract content from the PDF
    exam_content = extract_pdf_content(examPDF_path)
    if not exam_content:
        print("Halting execution due to PDF reading error.")
        return  # Exit if the PDF could not be read

    # 2. Send the Request and Get a Response
    try:
        print("Sending request to Azure OpenAI...")

        # Create the chat completion request with the extracted PDF content
        response = client.chat.completions.create(
            model=deployment_name,  # The model is your deployment name
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"subject: {subject}\ncommunity: {community}\nexam example: {exam_content}",
                },
            ],
            temperature=1,  # A lower temperature is often better for instruction-following
        )

        # 3. Process and Save the Response
        if response.choices:
            message_content = response.choices[0].message.content

            print("\n--- Response from Azure OpenAI ---")
            print(message_content)
            print("--------------------------------\n")

            # 4. Store the response in the specified text file
            try:
                with open(agentPrompt_path, "w", encoding="utf-8") as f:
                    f.write(message_content)
                print(f"✅ Successfully saved the agent prompt to: {agentPrompt_path}")
            except Exception as e:
                print(f"Error saving the file: {e}")

        else:
            print("No response received from the API.")

    except Exception as e:
        print(f"An API error occurred: {e}")

path = os.path.join(
            os.path.dirname(__file__), "..", f"prompts/"
        )


path_to_exam = os.path.join(
            os.path.dirname(__file__), "..", f"docs/philosofy_exams/"
        )



# Get all PDF files
pdf_files = [f for f in os.listdir(path_to_exam) if f.endswith('.pdf')]

# Execute the function for each PDF
for pdf_file in pdf_files:
    # Create full path
    pdf_path = os.path.join(path_to_exam, pdf_file)
    
    # Get filename without extension
    pdf_name = pdf_file[:-4]    # Removes .pdf extension
    pdf_name_capitalized = pdf_name[0].upper() + pdf_name[1:] if pdf_name else pdf_name
    prompt_maker(
        "Historia de la Filosofía",
        pdf_name,           # 2nd argument: just the filename without .pdf
        str(pdf_path),      # 3rd argument: full path to the PDF
        f"{path}{pdf_name_capitalized}/philosofy_{pdf_name}.txt",
    )
    
    print(f"Processed: {pdf_name}")

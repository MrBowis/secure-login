import os
import sys
import joblib
import glob
import re

# ==============================================================================
# CONFIGURACIÓN DE PATRONES HEURÍSTICOS (Frontend + Backend)
# ==============================================================================
PATRONES_PELIGROSOS = [
    # --- Frontend (JS/TS/React) ---
    (r'dangerouslySetInnerHTML', 'Posible XSS (React)'),
    (r'eval\(', 'Ejecución dinámica insegura'),
    (r'innerHTML', 'Manipulación directa del DOM (XSS)'),
    (r'document\.write', 'Escritura insegura en DOM'),
    # --- Backend (Python/SQL) ---
    (r'exec\(', 'Ejecución arbitraria de código (Python)'),
    (r'subprocess\.call\(.*shell=True', 'Inyección de comandos (Shell=True)'),
    (r'pickle\.load', 'Deserialización insegura'),
    (r'md5\(', 'Algoritmo de hash débil'),
    (r'sha1\(', 'Algoritmo de hash débil'),
    (r'cursor\.execute\(.*\%s.*\%', 'Posible Inyección SQL (Formato incorrecto)'),
    (r'f"SELECT.*\{', 'Posible Inyección SQL (f-string en query)'),
    # --- General (Secretos) ---
    (r'AWS_ACCESS_KEY_ID\s*=\s*[\'"]AKIA', 'Credencial AWS hardcodeada'),
    (r'BEGIN RSA PRIVATE KEY', 'Clave privada hardcodeada'),
]

print("📦 Cargando modelo de IA y vectorizador...")

# Asegúrate de que estos archivos existan en el repo o descárgalos antes
MODEL_PATH = 'modelo_xgb_seguridad.pkl'
VECT_PATH = 'vectorizador_tfidf.pkl'

if not os.path.exists(MODEL_PATH) or not os.path.exists(VECT_PATH):
    print(f"❌ Error: No se encuentran los archivos del modelo ({MODEL_PATH}, {VECT_PATH})")
    # En un entorno real, aquí podrías descargar los modelos de un bucket S3 o similar
    sys.exit(1)

try:
    model_cargado = joblib.load(MODEL_PATH)
    vectorizer_cargado = joblib.load(VECT_PATH)
    print("✅ Modelos cargados exitosamente")
except Exception as e:
    print(f"❌ Error crítico cargando modelos: {e}")
    sys.exit(1)

def identificar_lineas_sospechosas(codigo):
    hallazgos = []
    lineas = codigo.split('\n')
    for i, linea in enumerate(lineas):
        linea_num = i + 1
        contenido = linea.strip()
        if len(contenido) < 5 or contenido.startswith(('#', '//', '/*')):
            continue
        for patron, motivo in PATRONES_PELIGROSOS:
            if re.search(patron, contenido, re.IGNORECASE):
                muestra = (contenido[:80] + '...') if len(contenido) > 80 else contenido
                hallazgos.append(f"   ⚠️  Línea {linea_num}: {muestra} -> [{motivo}]")
                break
    return hallazgos

def probar_codigo(codigo, archivo):
    try:
        # Vectorizar y predecir
        X_test = vectorizer_cargado.transform([codigo])
        pred = model_cargado.predict(X_test)[0]
        prob = model_cargado.predict_proba(X_test)[0]
        # Asumiendo que la clase 1 es "Vulnerable"
        es_vulnerable = (pred == 1)
        prob_vulnerable = prob[1] * 100
        return es_vulnerable, prob_vulnerable
    except Exception as e:
        print(f"⚠️ Error analizando {archivo}: {e}")
        return False, 0.0

def escanear_proyecto():
    archivos_vulnerables = []
    
    # 1. Definir extensiones a buscar (Frontend + Backend)
    extensiones = [
        '**/*.py',      # Backend FastAPI
        '**/*.ts',      # Frontend Lógica
        '**/*.tsx',     # Frontend Componentes
        '**/*.js',      # Scripts generales
    ]
    
    files = []
    for ext in extensiones:
        files.extend(glob.glob(ext, recursive=True))
    
    # 2. Filtrar archivos de sistema/librerías
    ignorados = ['node_modules', 'venv', '.git', '.next', '__pycache__', 'test', 'tests', 'migrations']
    files_filtrados = []
    for f in files:
        if not any(ign in f for ign in ignorados):
            files_filtrados.append(f)

    print(f"🔍 Analizando {len(files_filtrados)} archivos de código fuente...")

    for file_path in files_filtrados:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                contenido = f.read()
            
            if not contenido.strip(): continue

            es_vuln, prob = probar_codigo(contenido, file_path)

            # Umbral de decisión (puedes ajustarlo, ej: > 50%)
            if es_vuln:
                print(f"🔴 VULNERABLE: {file_path} (Confianza IA: {prob:.2f}%)")
                detalles = identificar_lineas_sospechosas(contenido)
                
                # Solo reportamos si la IA dice vulnerable Y encontramos patrones (Opcional: o si la prob es muy alta)
                if detalles or prob > 80:
                    archivos_vulnerables.append({
                        'archivo': file_path,
                        'probabilidad': prob,
                        'lineas': detalles
                    })
                    for d in detalles: print(d)
                    print("-" * 40)

        except Exception as e:
            pass

    return archivos_vulnerables

if __name__ == "__main__":
    vulnerables = escanear_proyecto()

    if vulnerables:
        print(f"\n❌ FALLO: Se detectaron {len(vulnerables)} archivos vulnerables.")
        
        with open("security_report.txt", "w", encoding="utf-8") as f:
            f.write("### 🧠 Reporte de Seguridad (IA)\n\n")
            for v in vulnerables:
                f.write(f"- **{v['archivo']}** (Riesgo: {v['probabilidad']:.1f}%)\n")
                if v['lineas']:
                    f.write("  ```bash\n")
                    for l in v['lineas']: f.write(f"{l}\n")
                    f.write("  ```\n")
                else:
                    f.write("  > Detectado por análisis semántico del modelo (sin patrones obvios).\n")
                f.write("\n")
        
        sys.exit(1) # Rompe el pipeline
    else:
        print("\n✅ ANÁLISIS COMPLETADO: El código parece seguro.")
        sys.exit(0)
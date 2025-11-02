# T.E.S.T. Python Runner

Un wrapper de Python para ejecutar endpoints de T.E.S.T. (Toxicity Estimation Software Tool) con procesamiento concurrente y configuración flexible.

## Uso

```bash
python3 run_test.py [-h] [--smiles SMILES] [--smiles-file SMILES_FILE] [--java JAVA] [--workers WORKERS] [--timeout TIMEOUT] [--output-json OUTPUT_JSON] [--output-csv OUTPUT_CSV] [--calculate CALCULATE] [--tmp-dir TMP_DIR] [--keep-tmp]
                   [--wait-timeout WAIT_TIMEOUT] [--no-xvfb]
```

## Descripción

Ejecuta endpoints de T.E.S.T. de forma concurrente con configuración flexible

## Opciones

- `-h, --help`: Muestra este mensaje de ayuda y sale
- `--smiles SMILES, -s SMILES`: Cadena SMILES (se puede repetir)
- `--smiles-file SMILES_FILE, -f SMILES_FILE`: Ruta al archivo SMILES (uno por línea, se puede repetir)
- `--java JAVA`: Ruta al binario de java
- `--workers WORKERS, -w WORKERS`: Número de workers concurrentes
- `--timeout TIMEOUT`: Timeout por endpoint en segundos
- `--output-json OUTPUT_JSON, -o OUTPUT_JSON`: Escribir JSON final a archivo (por defecto stdout)
- `--output-csv OUTPUT_CSV`: Escribir resultados a archivo CSV (una molécula por fila, endpoints como columnas)
- `--calculate CALCULATE`: Lista separada por comas de endpoints a calcular. Disponibles: BCF, BP, Density, DevTox, ER_Binary, FP, IGC50, LC50, LC50DM, LD50, MP, Mutagenicity, ST, TC, VP, WS, viscosity. Si no se especifica, se calculan todos los endpoints.
- `--tmp-dir TMP_DIR`: Usar directorio temporal existente
- `--keep-tmp`: Mantener archivos temporales para depuración (por defecto: eliminar después de completar)
- `--wait-timeout WAIT_TIMEOUT`: Tiempo máximo para esperar archivos de salida en segundos (por defecto: 3600 = 1 hora)
- `--no-xvfb`: Deshabilitar wrapper xvfb-run (ejecutar Java directamente sin framebuffer virtual X)

## Ejemplos

```bash
# Uso básico con cadenas SMILES
python3 run_test.py --smiles 'CCO' --smiles 'c1ccccc1' > results.json

# Usando archivo SMILES con endpoints específicos y salida CSV
python3 run_test.py --smiles-file mols.smi --calculate 'BP,VP,WS' --output-csv results.csv

# Configuración personalizada con ruta específica de Java y workers
python3 run_test.py -s 'CCO' -w 8 --java /usr/bin/java -o output.json
```

## Endpoints Disponibles

Los siguientes endpoints están disponibles para cálculo:

| Endpoint     | Nombre                             | Unidad  | Descripción                                                                |
| ------------ | ---------------------------------- | ------- | -------------------------------------------------------------------------- |
| LC50         | 96h Fathead Minnow LC50            | mg/L    | Concentración letal para el 50% de Pimephales promelas (pez) tras 96 horas |
| LC50DM       | 48h Daphnia magna LC50             | mg/L    | Concentración letal para el 50% de pulgas de agua tras 48 horas            |
| IGC50        | Tetrahymena pyriformis IGC50       | mg/L    | Concentración que inhibe el crecimiento del 50% de protozoos               |
| LD50         | Oral Rat LD50                      | mg/kg   | Dosis letal oral para el 50% de ratas                                      |
| BCF          | Bioconcentration Factor            | L/kg    | Factor de bioacumulación en peces (log BCF)                                |
| DevTox       | Developmental Toxicity             | Binario | Probabilidad de toxicidad del desarrollo (sí/no)                           |
| Mutagenicity | Ames Mutagenicity                  | Binario | Potencial mutagénico (prueba de Ames)                                      |
| BP           | Boiling Point                      | °C      | Temperatura de ebullición                                                  |
| Density      | Density                            | g/cm³   | Densidad a 25°C                                                            |
| FP           | Flash Point                        | °C      | Temperatura de inflamación                                                 |
| MP           | Melting Point                      | °C      | Temperatura de fusión                                                      |
| ST           | Surface Tension                    | mN/m    | Tensión superficial                                                        |
| TC           | Thermal Conductivity               | W/m·K   | Conductividad térmica                                                      |
| VP           | Vapor Pressure                     | mmHg    | Presión de vapor a 25°C (log VP)                                           |
| WS           | Water Solubility                   | mg/L    | Solubilidad en agua a 25°C (log WS)                                        |
| viscosity    | Viscosity                          | cP      | Viscosidad dinámica                                                        |
| ER_Binary    | Estrogen Receptor Binding (Binary) | Binario | Unión al receptor de estrógeno (sí/no)                                     |

## Requisitos

- Python 3.x
- Java (para ejecutar el archivo JAR de T.E.S.T.)
- WebTEST.jar (debe estar en el mismo directorio que el script)

## Formatos de Salida

### Salida JSON

La herramienta produce resultados en formato JSON con la siguiente estructura:

- `molecules`: Diccionario que contiene resultados para cada molécula
- `metadata`: Información sobre la ejecución (endpoints solicitados, tiempo de ejecución, etc.)
- `diagnostics`: Información de tiempo de ejecución y estadísticas

### Salida CSV

Al usar `--output-csv`, los resultados se escriben en formato tabular con:

- Una fila por molécula
- SMILES en la primera columna
- Una columna por endpoint solicitado
- Valores predichos o "NA"/"ERROR" para predicciones fallidas

## Estructura del Módulo

- `run_test.py`: Punto de entrada principal
- `test/cli.py`: Manejo de interfaz de línea de comandos
- `test/core.py`: Funcionalidad principal y ejecutor de T.E.S.T.
- `test/config.py`: Configuración y descripciones de endpoints
- `test/models.py`: Modelos de datos para resultados
- `test/utils.py`: Funciones de utilidad

## Notas

- La herramienta usa procesamiento concurrente para acelerar los cálculos cuando se solicitan múltiples endpoints
- Los archivos temporales se crean durante la ejecución y se limpian automáticamente (a menos que se use `--keep-tmp`)
- En sistemas Linux, `xvfb-run` se usa por defecto para proporcionar una pantalla virtual para la aplicación Java (se puede deshabilitar con `--no-xvfb`)

Debe existir WebTEST.jar en el mismo directorio que el script esto se ignora en git así que hay que obtenerlo por otros medios por ejemplo en los releases de este repositorio
igual que la databases igual estará en el mismo directorio que el script y se ignora en git ya que pesan mucho

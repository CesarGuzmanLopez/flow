"""
Configuration module for T.E.S.T. endpoints and settings.
"""

# Embedded endpoint descriptions (extracted from explicacion.md table)
ENDPOINTS_DESCRIPTION = {
    "LC50": {
        "name": "96h Fathead Minnow LC50",
        "unit": "mg/L",
        "description": (
            "Concentración letal para el 50% de Pimephales promelas "
            "(pez) tras 96 horas."
        ),
        "application": "Toxicidad aguda acuática",
    },
    "LC50DM": {
        "name": "48h Daphnia magna LC50",
        "unit": "mg/L",
        "description": "Concentración letal para el 50% de pulgas de agua tras 48 horas.",
        "application": "Toxicidad aguda a invertebrados acuáticos",
    },
    "IGC50": {
        "name": "Tetrahymena pyriformis IGC50",
        "unit": "mg/L",
        "description": "Concentración que inhibe el crecimiento del 50% de protozoos.",
        "application": "Toxicidad crónica a microorganismos",
    },
    "LD50": {
        "name": "Oral Rat LD50",
        "unit": "mg/kg",
        "description": "Dosis letal oral para el 50% de ratas.",
        "application": "Toxicidad aguda sistémica",
    },
    "BCF": {
        "name": "Bioconcentration Factor",
        "unit": "L/kg",
        "description": "Factor de bioacumulación en peces (log BCF).",
        "application": "Potencial de bioacumulación",
    },
    "DevTox": {
        "name": "Developmental Toxicity",
        "unit": "Binario",
        "description": "Probabilidad de toxicidad del desarrollo (sí/no).",
        "application": "Riesgo reproductivo",
    },
    "Mutagenicity": {
        "name": "Ames Mutagenicity",
        "unit": "Binario",
        "description": "Potencial mutagénico (prueba de Ames).",
        "application": "Carcinogenicidad/genotoxicidad",
    },
    "BP": {
        "name": "Boiling Point",
        "unit": "°C",
        "description": "Temperatura de ebullición.",
        "application": "Propiedad fisicoquímica",
    },
    "Density": {
        "name": "Density",
        "unit": "g/cm³",
        "description": "Densidad a 25°C.",
        "application": "Propiedad fisicoquímica",
    },
    "FP": {
        "name": "Flash Point",
        "unit": "°C",
        "description": "Temperatura de inflamación.",
        "application": "Seguridad química",
    },
    "MP": {
        "name": "Melting Point",
        "unit": "°C",
        "description": "Temperatura de fusión.",
        "application": "Estabilidad térmica",
    },
    "ST": {
        "name": "Surface Tension",
        "unit": "mN/m",
        "description": "Tensión superficial.",
        "application": "Comportamiento interfacial",
    },
    "TC": {
        "name": "Thermal Conductivity",
        "unit": "W/m·K",
        "description": "Conductividad térmica.",
        "application": "Transferencia de calor",
    },
    "VP": {
        "name": "Vapor Pressure",
        "unit": "mmHg",
        "description": "Presión de vapor a 25°C (log VP).",
        "application": "Volatilidad",
    },
    "WS": {
        "name": "Water Solubility",
        "unit": "mg/L",
        "description": "Solubilidad en agua a 25°C (log WS).",
        "application": "Biodisponibilidad",
    },
    "viscosity": {
        "name": "Viscosity",
        "unit": "cP",
        "description": "Viscosidad dinámica.",
        "application": "Flujo y transporte",
    },
    "ER_Binary": {
        "name": "Estrogen Receptor Binding (Binary)",
        "unit": "Binario",
        "description": "Unión al receptor de estrógeno (sí/no).",
        "application": "Disrupción endocrina",
    },
}

DEFAULT_WORKERS = 6
DEFAULT_WAIT_TIMEOUT = 3600  # 1 hour

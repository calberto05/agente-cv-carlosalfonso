# Anexo A — Esquema del JSON de CV

Estructura completa del JSON generado por el pipeline a partir de un PDF de CV.

---

## Estructura raíz

```json
{
  "personal_info": { ... },
  "experience":    [ ... ],
  "education":     [ ... ],
  "skills":        { ... },
  "projects":      [ ... ],
  "certifications":[ ... ],
  "hackathons":    [ ... ],
  "languages":     [ ... ],
  "extra_sections":[ ... ]
}
```

---

## `personal_info`

```json
{
  "name":     "Carlos Alfonso Alberto",
  "email":    "correo@ejemplo.com",
  "phone":    "+52 55 1234 5678",
  "linkedin": "https://linkedin.com/in/usuario",
  "github":   "https://github.com/usuario",
  "location": "Ciudad de México, México",
  "summary":  "Resumen profesional extraído del CV."
}
```

---

## `experience`

```json
[
  {
    "company":      "Nombre de la empresa",
    "role":         "Título del puesto",
    "start_date":   "Enero 2023",
    "end_date":     "Presente",
    "description":  "Descripción de responsabilidades y logros.",
    "technologies": ["Python", "FastAPI", "GCP"]
  }
]
```

---

## `education`

```json
[
  {
    "institution": "Universidad Nacional Autónoma de México",
    "degree":      "Licenciatura",
    "field":       "Ingeniería en Computación",
    "start_date":  "2018",
    "end_date":    "2023"
  }
]
```

---

## `skills`

```json
{
  "programming_languages": ["Python", "JavaScript", "SQL"],
  "frameworks":            ["FastAPI", "React", "LangChain"],
  "tools":                 ["Docker", "Git", "Terraform"],
  "cloud":                 ["Google Cloud", "Cloud Run", "Vertex AI"],
  "other":                 ["Machine Learning", "Agile"]
}
```

---

## `projects`

```json
[
  {
    "name":         "Nombre del proyecto",
    "description":  "Descripción del proyecto.",
    "technologies": ["Python", "Gemini"],
    "url":          "https://proyecto.com",
    "github_repo":  "usuario/repo"
  }
]
```

---

## `certifications`

```json
[
  {
    "name":   "Google Cloud Professional Data Engineer",
    "issuer": "Google",
    "date":   "2024",
    "url":    "https://credential.url"
  }
]
```

---

## `hackathons`

```json
[
  {
    "name":         "Nombre del hackathon",
    "organizer":    "Organizador",
    "date":         "2024",
    "description":  "Descripción del proyecto desarrollado.",
    "result":       "1er lugar",
    "technologies": ["Python", "Google ADK"]
  }
]
```

---

## `languages`

```json
[
  {
    "language":    "Español",
    "proficiency": "Nativo"
  },
  {
    "language":    "Inglés",
    "proficiency": "B2"
  }
]
```

---

## `extra_sections`

Captura cualquier sección del CV que no encaje en los campos estándar anteriores.

```json
[
  {
    "section_name": "Publicaciones",
    "content":      "Texto completo de la sección tal como aparece en el CV."
  },
  {
    "section_name": "Voluntariado",
    "content":      "..."
  }
]
```

---

## Notas

- Todos los campos de texto usan cadena vacía `""` si no están presentes en el CV.
- Todos los campos de lista usan `[]` si no hay datos.
- El schema es aplicado por Gemini vía `response_schema`, por lo que la estructura está garantizada en cada ejecución.

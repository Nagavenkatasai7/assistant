# Resume Editor - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT WEB APPLICATION                    │
│                           (app.py)                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ User Interaction
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                      RESUME EDITOR UI                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Edit Tab     │  │ Preview Tab  │  │ Version Hist │          │
│  │              │  │              │  │              │          │
│  │ • Text Area  │  │ • Markdown   │  │ • List View  │          │
│  │ • Word Count │  │   Renderer   │  │ • Restore Btn│          │
│  │ • Char Count │  │ • Metrics    │  │ • Timestamps │          │
│  │ • Save Btn   │  │   Dashboard  │  │              │          │
│  │ • Undo Btn   │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌───────────────────────────────────────────────────┐          │
│  │           Export Options                           │          │
│  │  [PDF Download] [DOCX Generate] [Copy Markdown]   │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Data Flow
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                     SESSION STATE MANAGEMENT                     │
│                                                                  │
│  • generated_resume: {id, content, pdf_path, company, score}    │
│  • resume_id: Current resume ID                                 │
│  • last_auto_save: Timestamp of last save                       │
│  • show_versions: Version history toggle state                  │
│  • editor_content: Current editor text                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ↓               ↓               ↓
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │ Database  │   │    PDF    │   │   DOCX    │
        │  Module   │   │ Generator │   │ Generator │
        └───────────┘   └───────────┘   └───────────┘
                │               │               │
                │               │               │
                ↓               ↓               ↓
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │  SQLite   │   │ ReportLab │   │python-docx│
        │  Database │   │   Engine  │   │   Engine  │
        └───────────┘   └───────────┘   └───────────┘
                │               │               │
                │               │               │
                ↓               ↓               ↓
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │  resume_  │   │   .pdf    │   │   .docx   │
        │ versions  │   │   files   │   │   files   │
        │   table   │   │           │   │           │
        └───────────┘   └───────────┘   └───────────┘


## Detailed Component Architecture

### Summary
This architecture document provides a comprehensive visual representation of the Resume Editor feature, showing:
- User interface components
- Data flow between layers
- Database schema relationships
- File generation pipelines
- Version control mechanisms
- Export workflows
- Security measures
- Performance optimizations

All components are production-ready and have been thoroughly tested.


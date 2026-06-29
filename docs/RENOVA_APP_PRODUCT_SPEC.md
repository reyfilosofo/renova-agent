# Renova App Product Specification

## Product name

Renova Open System App

## Product type

Functional web application for Replit, not a static website.

## Purpose

The app presents Renova as a usable public technology: a living interface where people can understand the philosophy, run a renewal assessment, explore a conceptual graph, consult a local agent scaffold, and generate a practical lab canvas.

## Primary users

- students and teachers
- cultural managers
- researchers
- community facilitators
- institutions
- civic labs
- creative teams
- people discovering Renova for the first time

## Core modules

### 1. Home dashboard

A sober application shell with a navigation sidebar and five cards:

- Open Corpus
- Renova Agent
- Renova Index
- Renovagrama
- Lab Kit

The dashboard must feel like a research instrument, not a marketing landing page.

### 2. Renova Index

Interactive assessment form with five dimensions:

- habitat
- repair
- horizon
- sensitivity
- equilibrium

Each dimension receives a 0-100 score and an evidence note. The app calculates the IRG result, qualitative level, diagnostic buckets, and recommended actions.

### 3. Renova Agent

A local scaffold chat interface. The first version can be rule-based and must explain that it does not replace professional advice. It should answer questions about Renova, institutions, schools, communities, culture, care, and renewal.

### 4. Renovagrama

A visual concept map showing nodes and relations from the Renova ontology. The first version can use a simple interactive graph or a readable node list if graph rendering is not available.

### 5. Open Corpus

A searchable glossary and public corpus panel with definitions, tags, and short explanations.

### 6. Lab Kit

A workshop canvas generator. The user enters a subject such as school, community, cultural project, or institution, and receives a structured facilitation canvas.

## Design direction

The visual system should be serious, philosophical, institutional, and contemporary:

- deep blue or near-black base
- ivory or off-white reading surfaces
- restrained gold accents
- clean typography
- high readability
- no childish aesthetics
- no generic startup look

## Minimum viable data

Use the repository data and concepts already present:

- sample assessment
- glossary
- ontology nodes
- Renova Index formula
- Renova Agent principles
- Lab Kit prompts

## Success criteria

- user can complete an assessment and obtain an IRG result
- user can ask the Renova Agent a question
- user can browse the core concepts
- user can generate a lab canvas
- user understands Renova as open cultural technology
- the app is usable on mobile and desktop

## Platform plan

- GitHub remains the source of truth.
- Replit is the main executable app environment.
- Lovable is used for a parallel visual prototype and UI acceleration.
- Wix is not used as a replacement for the app. It can later link to the app or embed it from the existing Renova/Wix presence.
